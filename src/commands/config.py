import logging
from datetime import datetime

from discord.bot import Bot
from discord.commands import ApplicationContext

import src.repos.firebase_repo as repo
from src.model.database import Match, Player, PlayerEloHistory, Season, Team, TeamSide
from src.repos import elo_repo, match_repo, player_repo, season_repo
from src.repos.database import get_session

logging.basicConfig(format="%(levelname)s %(name)s %(asctime)s: %(message)s", level=logging.INFO)
logger = logging.getLogger("c/config")


def register_config_commands(bot: Bot):
    @bot.slash_command(name="migrate", description="Migra os dados para sqlite")
    async def migrate(ctx: ApplicationContext):
        await ctx.response.defer()
        with next(get_session()) as session:
            if not ctx.user.guild_permissions.administrator:
                await ctx.followup.send("Somente admins podem usar esse comando")
                return

            players = await repo.get_players()

            players_dict = {}

            for player in players:
                db_player = player_repo.create_player(
                    session, Player(username=player.get("nome"), discord_id=str(player.get("discord_id")))
                )
                players_dict[player.id] = db_player

            matches = await repo.get_all_finished_matches()
            for match in matches:
                blue_team = match.get("blue_team")

                blue_players = [players_dict[p] for p in blue_team["players"]]

                blue_team_db = Team(
                    side=TeamSide.blue, players=blue_players, champions=blue_team["champions"], team_rating=1500
                )

                red_team = match.get("red_team")

                red_players = [players_dict[p] for p in red_team["players"]]

                red_team_db = Team(
                    side=TeamSide.red, players=red_players, champions=red_team["champions"], team_rating=1500
                )

                new_match = Match(
                    mode=match.get("mode"),
                    result=match.get("result").lower(),
                    teams=[blue_team_db, red_team_db],
                    created_at=datetime.fromisoformat(match.get("timestamp").isoformat()),
                )

                match_repo.create(session, new_match)

            await ctx.followup.send("Dados migrados!")

    @bot.slash_command(name="reset", description="Cria uma nova season e reinicia os elos")
    async def reset(ctx: ApplicationContext):
        await ctx.response.defer()
        with next(get_session()) as session:
            if not ctx.user.guild_permissions.administrator:
                await ctx.followup.send("Somente admins podem usar esse comando")
                return

            players = player_repo.get_all_players(session)

            for player in players:
                points_before_update = player.points
                player.points = 1500

                history_entry = PlayerEloHistory(
                    player_id=player.id, match_id=None, points_before=points_before_update, points_after=player.points
                )

                elo_repo.create_history(session, history_entry)

                player_repo.update_player(session, player)

            season_repo.create_season(session, Season())
