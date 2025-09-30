import logging

from shared.model.database import PlayerEloHistory, PlayerSeasonFinalElo, Season
from shared.repos import elo_repo, player_repo, season_repo

logger = logging.getLogger("c/match_service")


class ConfigService:
    def __init__(self):
        self._elo_repo = elo_repo
        self._player_repo = player_repo
        self._season_repo = season_repo

    def reset_elo(self, session):
        players = self._player_repo.get_all_players_ranked(session)
        season = self._season_repo.get_last_season(session)

        for player in players:
            points_before_update = player.points
            player.points = 1500

            history_entry = PlayerEloHistory(
                player_id=player.id,
                match_id=None,
                points_before=points_before_update,
                points_after=player.points,
                change=player.points - points_before_update,
            )

            season_elo_entry = PlayerSeasonFinalElo(
                player_id=player.id, season_id=season.id, points=points_before_update
            )

            self._elo_repo.create_history(session, history_entry)
            self._elo_repo.create_season_history(session, season_elo_entry)

            self._player_repo.update_player(session, player)

        season_repo.create_season(session, Season())
