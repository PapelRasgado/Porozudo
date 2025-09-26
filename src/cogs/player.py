import logging

import aiohttp
import discord
from discord import Cog
from discord.ext import commands

from src.main import PorozudoBot
from src.model.database import Player
from src.repos import player_repo
from src.repos.database import get_session

logger = logging.getLogger("c/player")


class PlayerCog(Cog):
    def __init__(self, bot: PorozudoBot):
        self.bot = bot
        self.riot_client = bot.riot_client

    @commands.slash_command(name="registrar", description="Adicionar jogador")
    async def register_new_player(self, ctx, nome: str, user: discord.User):
        await ctx.response.defer(ephemeral=True)
        with next(get_session()) as session:
            player_repo.create_player(session, Player(username=nome, discord_id=str(user.id)))
            await ctx.followup.send(f"{nome} registrado com sucesso.")

    @commands.slash_command(name="conectarriot", description="Conecta a conta do usuário com o id da conta riot")
    async def connect_riot(self, ctx, game_name: str, tag_line: str):
        await ctx.response.defer(ephemeral=True)
        with next(get_session()) as session:
            try:
                player_data = await self.riot_client.get_puuid_by_riot_name(game_name, tag_line)
                player = player_repo.get_player_by_discord(session, str(ctx.author.id))

                player.puuid = player_data.puuid

                player_repo.update_player(session, player)

                logger.info(f"Account linked: {player.id} -> {player.puuid}.")

                await ctx.followup.send("Conta linkada com sucesso.")
            except aiohttp.ClientResponseError as e:
                if e.status == 404:
                    await ctx.followup.send(f"Jogador com nick {game_name}#{tag_line} não encontrado.")
                else:
                    await ctx.followup.send("Falha ao buscar informações sobre o jogador.")


def setup(bot):
    bot.add_cog(PlayerCog(bot))
