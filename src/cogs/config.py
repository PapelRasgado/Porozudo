import logging
from datetime import datetime, time

from discord import Activity, ActivityType, Cog
from discord.commands import ApplicationContext
from discord.ext import commands, tasks

import src.repos.firebase_repo as repo
from src.main import PorozudoBot
from src.model.database import Match, Player, PlayerEloHistory, Season, Team, TeamSide
from src.repos import elo_repo, match_repo, player_repo, season_repo
from src.repos.database import get_session

logging.basicConfig(format="%(levelname)s %(name)s %(asctime)s: %(message)s", level=logging.INFO)
logger = logging.getLogger("c/config")


class ConfigCog(Cog):
    def __init__(self, bot: PorozudoBot):
        self.bot = bot
        self.daily_champion_update.start()

    def cog_unload(self):
        self.daily_champion_update.cancel()

    @Cog.listener()
    async def on_ready(self):
        logger.info(f"{self.bot.user} tá on pai!")
        await self.bot.change_presence(
            activity=Activity(type=ActivityType.custom, name="custom", state="Fraudando as runas....")
        )

    @tasks.loop(time=time(hour=6, minute=0, second=0))
    async def daily_champion_update(self):
        logger.info("Atualizando dados dos campeões...")
        try:
            self.bot.champion_data.update_data()
            logger.info("Dados dos campeões atualizados.")
        except Exception as e:
            logger.error(f"Falha ao atualizar dados dos campeões: {e}")

    @commands.slash_command(name="migrar", description="Migra os dados para sqlite")
    async def migrate(self, ctx: ApplicationContext):
        await ctx.response.defer()
        with next(get_session()) as session:
            if not ctx.guild_id:
                await ctx.followup.send("Esse comando deve ser usado em um servidor")
                return

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

    @commands.slash_command(name="reset", description="Cria uma nova season e reinicia os elos")
    async def reset(self, ctx: ApplicationContext):
        await ctx.response.defer()
        with next(get_session()) as session:
            if not ctx.guild_id:
                await ctx.followup.send("Esse comando deve ser usado em um servidor")
                return

            if not ctx.user.guild_permissions.administrator:
                await ctx.followup.send("Somente admins podem usar esse comando")
                return

            players = player_repo.get_all_players(session)

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

                elo_repo.create_history(session, history_entry)

                player_repo.update_player(session, player)

            season_repo.create_season(session, Season())


def setup(bot):
    bot.add_cog(ConfigCog(bot))
