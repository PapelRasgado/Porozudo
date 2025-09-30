import logging

import discord
from discord.ext import commands

logger = logging.getLogger("c/events")


class EventsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        command_name = ctx.command.name if ctx.command else "Unknown command"

        logger.exception(f"Error on command '{command_name}':", exc_info=error)

        embed = discord.Embed(
            title="😕 Ops! Ocorreu um Erro",
            description="Algo inesperado aconteceu ao executar o comando!",
            color=discord.Color.red(),
        )
        embed.set_footer(text="Se o problema persistir, por favor, entre em contato com um administrador.")

        if ctx.interaction.response.is_done():
            await ctx.followup.send(embed=embed)
        else:
            await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(EventsCog(bot))
