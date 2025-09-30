import logging
from datetime import datetime, time

from discord import Activity, ActivityType, Cog
from discord.commands import ApplicationContext
from discord.ext import commands, tasks

from bot.main import PorozudoBot
from bot.service.config_service import ConfigService
from shared.repos.database import get_session

logger = logging.getLogger("c/config")


class ConfigCog(Cog):
    def __init__(self, bot: PorozudoBot):
        self.bot = bot
        self.config_service = ConfigService()

        self.daily_champion_update.start()
        self.monthly_season_reset.start()

    def cog_unload(self):
        self.daily_champion_update.cancel()
        self.monthly_season_reset.cancel()

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

    @tasks.loop(time=time(hour=1, minute=0, second=0))
    async def monthly_season_reset(self):
        today = datetime.now().date()
        if today.day == 1:
            with next(get_session()) as session:
                self.config_service.reset_elo(session)

    @commands.slash_command(name="reset", description="Cria uma nova season e reinicia os elos")
    async def reset(self, ctx: ApplicationContext):
        await ctx.response.defer()

        if not ctx.guild_id:
            await ctx.followup.send("Esse comando deve ser usado em um servidor")
            return

        if not ctx.user.guild_permissions.administrator:
            await ctx.followup.send("Somente admins podem usar esse comando")
            return

        with next(get_session()) as session:
            self.config_service.reset_elo(session)
            await ctx.followup.send("Nova season iniciada!")


def setup(bot):
    bot.add_cog(ConfigCog(bot))
