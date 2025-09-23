import logging
from datetime import time

from discord import Activity, ActivityType, Cog
from discord.commands import ApplicationContext
from discord.ext import commands, tasks

from src.main import PorozudoBot
from src.model.database import PlayerEloHistory, Season
from src.repos import elo_repo, player_repo, season_repo
from src.repos.database import get_session

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
