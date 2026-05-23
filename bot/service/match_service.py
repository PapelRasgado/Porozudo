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
    expected_score = 1 / (
            1 + 10 ** ((opponent_team_rating - player_rating) / 400)
    )

    raw_change = round(
        k_factor * (1 - expected_score)
    )

    raw_change = max(1, raw_change)

    direction = 1 if won else -1

    return raw_change * direction


class MatchService:
    def __init__(self):
        self._elo_repo = elo_repo
        self._match_repo = match_repo
        self._player_repo = player_repo
        self._player_champion_repo = player_champion_repo

    def finalize_match(self, session, match: Match, result: TeamSide):
        blue_team = next((t for t in match.teams if t.side == TeamSide.blue), None)
        red_team = next((t for t in match.teams if t.side == TeamSide.red), None)

        if result == TeamSide.blue:
            winning_team_obj, losing_team_obj = blue_team, red_team
        else:
            winning_team_obj, losing_team_obj = red_team, blue_team

        k_factor = {1: 1, 2: 1, 3: 5, 4: 10, 5: 20}.get(match.mode, 10)

        for player in winning_team_obj.players:
            point_change = _calculate_elo_change(player.points, losing_team_obj.team_rating, k_factor, True)
            points_before = player.points
            player.points += point_change
            history = PlayerEloHistory(
                player_id=player.id,
                match_id=match.id,
                points_before=points_before,
                points_after=player.points,
                change=point_change,
            )
            self._elo_repo.create_history(session, history)

        for player in losing_team_obj.players:
            point_change = _calculate_elo_change(player.points, winning_team_obj.team_rating, k_factor, False)
            points_before = player.points
            player.points -= point_change
            history = PlayerEloHistory(
                player_id=player.id,
                match_id=match.id,
                points_before=points_before,
                points_after=player.points,
                change=-point_change,
            )
            self._elo_repo.create_history(session, history)

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
