import logging

from shared.model.database import Match, PlayerEloHistory, PlayerMatchChampion, TeamSide
from shared.model.riot import ActiveGameSchema
from shared.repos import elo_repo, match_repo, player_champion_repo, player_repo
from shared.repos.database import get_session

logger = logging.getLogger("c/match_service")


def _calculate_elo_change(
    player_rating: int,
    opponent_team_rating: float,
    k_factor: int,
    won: bool,
) -> int:
    expected_score = 1 / (1 + 10 ** ((opponent_team_rating - player_rating) / 400))

    actual_score = 1 if won else 0

    change = round(k_factor * (actual_score - expected_score))

    return max(1, change) if won else min(-1, change)


class MatchService:
    def __init__(self):
        self._elo_repo = elo_repo
        self._match_repo = match_repo
        self._player_repo = player_repo
        self._player_champion_repo = player_champion_repo

    def finalize_match(self, session, match: Match, result: TeamSide):
        teams = {team.side: team for team in match.teams}

        k_factor = {
            1: 1,
            2: 1,
            3: 5,
            4: 10,
            5: 20,
        }.get(match.mode, 10)

        for side, team in teams.items():
            won = side == result

            opponent_team = teams[TeamSide.red if side == TeamSide.blue else TeamSide.blue]

            for player in team.players:
                point_change = _calculate_elo_change(
                    player_rating=player.points,
                    opponent_team_rating=opponent_team.team_rating,
                    k_factor=k_factor,
                    won=won,
                )

                points_before = player.points
                player.points += point_change

                self._elo_repo.create_history(
                    session,
                    PlayerEloHistory(
                        player_id=player.id,
                        match_id=match.id,
                        points_before=points_before,
                        points_after=player.points,
                        change=point_change,
                    ),
                )

        match.result = result
        self._match_repo.update(session, match)

        logger.info(f"Match {match.id} finished. Winner: {result.value}.")

    def revert_match(self, session, match: Match):
        for entry in match.elo_history:
            if not entry.is_reverted:
                player = player_repo.get_player_by_id(session, entry.player_id)
                if player:
                    logger.info(f"Revert {player.username}: {player.points} -> {player.points - entry.change})")
                    player.points -= entry.change
                    entry.is_reverted = True

        match.result = None
        self._match_repo.update(session, match)

        logger.info(f"Match {match.id} reverted.")

    def register_match_champions(self, match_id, active_game: ActiveGameSchema):
        with next(get_session()) as session:
            match = self._match_repo.get_by_id(session, match_id)

            if match.champions_registered:
                return

            participants_map = {p.puuid: p for p in active_game.participants}

            for team in match.teams:
                for player in team.players:
                    participant_data = participants_map.get(player.puuid)

                    if participant_data:
                        info = PlayerMatchChampion(
                            player_id=player.id, match_id=match_id, champion_id=str(participant_data.champion_id)
                        )
                        self._player_champion_repo.create_player_champion(session, info)

            match.champions_registered = True
            self._match_repo.update(session, match)
