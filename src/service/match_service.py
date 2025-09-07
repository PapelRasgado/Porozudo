import logging

from src.model.database import Match, PlayerEloHistory, PlayerMatchChampion, TeamSide
from src.model.riot import ActiveGameSchema
from src.repos import elo_repo, match_repo, player_champion_repo, player_repo
from src.repos.database import get_session

logging.basicConfig(format="%(levelname)s %(name)s %(asctime)s: %(message)s", level=logging.INFO)
logger = logging.getLogger("c/match_service")


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

        expected_win_prob = 1 / (1 + 10 ** ((losing_team_obj.team_rating - winning_team_obj.team_rating) / 400))
        point_change = round(k_factor * (1 - expected_win_prob))
        point_change = max(1, point_change)

        for player in winning_team_obj.players:
            points_before = player.points
            player.points += point_change
            history = PlayerEloHistory(
                player_id=player.id,
                match_id=match.id,
                points_before=points_before,
                points_after=player.points,
                change=point_change,
            )
            elo_repo.create_history(session, history)

        for player in losing_team_obj.players:
            points_before = player.points
            player.points -= point_change
            history = PlayerEloHistory(
                player_id=player.id,
                match_id=match.id,
                points_before=points_before,
                points_after=player.points,
                change=-point_change,
            )
            elo_repo.create_history(session, history)

        match_repo.update(session, match)
        logger.info(f"Match {match.id} finished. Winner: {result.value}. Elo change: +/- {point_change} points.")

    def revert_match(self, session, match: Match):
        for entry in match.elo_history:
            if not entry.is_reverted:
                player = player_repo.get_player_by_id(session, entry.player_id)
                if player:
                    logger.info(f"Revert {player.username}: {player.points} -> {player.points - entry.change})")
                    player.points -= entry.change
                    entry.is_reverted = True

        match.result = None
        match_repo.update(session, match)

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
                            player_id=player.id, match_id=match_id, champion_id=participant_data.champion_id
                        )
                        self._player_champion_repo.create_player_champion(session, info)

            match.champions_registered = True
            self._match_repo.update(session, match)
