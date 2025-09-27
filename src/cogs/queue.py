import discord
from discord import Cog
from discord.ext import commands

from src.main import PorozudoBot
from src.repos import config_repo, player_repo
from src.repos.database import get_session
from src.ui.views import DeleteButtons, TeamSelectView
from src.utils.embed import create_active_players_embed


class QueueCog(Cog):
    def __init__(self, bot: PorozudoBot):
        self.bot = bot

    @commands.slash_command(name="adicionar", description="Adiciona jogadores a lista de ativos")
    async def add_active_players(self, ctx: discord.ApplicationContext):
        await ctx.response.defer(ephemeral=True)

        if not ctx.user.guild_permissions.administrator:
            await ctx.followup.send("Somente admins podem usar esse comando")
            return

        await ctx.followup.send("Monta o time!", view=TeamSelectView())

    @commands.slash_command(
        name="canal", description="Adiciona os jogadores que estão em um determinado canal a lista de ativos"
    )
    async def add_channel_active_players(self, ctx: discord.ApplicationContext):
        await ctx.response.defer(ephemeral=True)
        with next(get_session()) as session:
            if not ctx.user.guild_permissions.administrator:
                await ctx.followup.send("Somente admins podem usar esse comando")
                return

            member = ctx.guild.get_member(ctx.user.id)
            voice = member.voice

            if not voice:
                await ctx.followup.send("É necessário estar conectado a um canal de voz para executar esse comando!")
                return

            players = player_repo.get_players_by_discord_ids(session, [str(uid) for uid in voice.channel.voice_states])
            config_repo.clear_player_pool(session)
            config_repo.add_to_pool(session, players)

            await ctx.followup.send(f"Os jogadores do canal {voice.channel.name} foram adicionados a lista de ativos!")

    @commands.slash_command(name="limpar", description="Apaga todos os jogadores da lista de ativos")
    async def clear_active_players(self, ctx):
        await ctx.response.defer(ephemeral=True)
        with next(get_session()) as session:
            if not ctx.user.guild_permissions.administrator:
                await ctx.followup.send("Somente admins podem usar esse comando")
                return

            config_repo.clear_player_pool(session)
            await ctx.followup.send("A lista de jogadores ativos foi esvaziada!")

    @commands.slash_command(name="ativos", description="Mostra os jogadores ativos")
    async def list_active_players(self, ctx):
        await ctx.response.defer()
        with next(get_session()) as session:
            if not ctx.user.guild_permissions.administrator:
                await ctx.followup.send("Somente admins podem usar esse comando")
                return

            players = config_repo.get_pool_players(session)
            embed = create_active_players_embed(players)
            await ctx.followup.send(embed=embed, view=DeleteButtons(players))


def setup(bot):
    bot.add_cog(QueueCog(bot))
