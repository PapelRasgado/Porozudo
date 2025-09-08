import logging

import discord
from discord import Cog, OptionChoice
from discord.commands import Option
from discord.ext import commands

from src.main import PorozudoBot
from src.model.database import Match, TeamSide
from src.repos import config_repo, match_repo, season_repo
from src.repos.database import get_session
from src.service.match_monitor import ActiveMatchMonitor
from src.service.match_service import MatchService
from src.team_generator.generator import generate_teams
from src.ui.views import ResultButtons
from src.utils.embed import create_champion_embed

logger = logging.getLogger("c/match")


async def send_embed(player_info, embed, bot):
    player_discord = await bot.fetch_user(player_info.discord_id)

    try:
        embed["file"].seek(0)
        file = discord.File(fp=embed["file"], filename="image.png")

        await player_discord.send(file=file, embed=embed["embed"])
    except Exception as e:
        logger.warning(f"Failed to send message to user {player_discord.name}, cause: {e}")


class MatchCog(Cog):
    def __init__(self, bot: PorozudoBot):
        self.bot = bot
        self.riot_client = bot.riot_client

        self.match_service = MatchService()
        self.match_monitor = ActiveMatchMonitor(riot_client=self.riot_client, match_service=self.match_service)

    @commands.slash_command(name="sortear", description="Sortea os times e campeões")
    async def create_match(
        self,
        ctx,
        choices_number: Option(int, "Quantidade de campeões", name="opções", default=0, min_value=1, max_value=10),
    ):
        await ctx.response.defer()
        if not ctx.guild_id:
            await ctx.followup.send("Esse comando deve ser usado em um servidor")
            return

        with next(get_session()) as session:
            players = config_repo.get_pool_players(session)

            try:
                teams = generate_teams(players, list(self.bot.champion_data.values()), choices_number)
            except ValueError as e:
                await ctx.followup.send(str(e))
                return

            season = season_repo.get_last_season(session)
            match = match_repo.create(session, Match(teams=teams, mode=len(teams[0].players), season=season))

            blue_team_db = teams[0] if teams[0].side == "blue" else teams[1]
            red_team_db = teams[1] if teams[1].side == "red" else teams[0]

            blue_embed = create_champion_embed(blue_team_db.champions, self.bot.champion_data, discord.Colour.blue(), 1)
            red_embed = create_champion_embed(red_team_db.champions, self.bot.champion_data, discord.Colour.red(), 2)

            blue_team_players = ""
            for idx, player in enumerate(blue_team_db.players):
                blue_team_players += f"{idx + 1} - <@{player.discord_id}>\n"
                await send_embed(player, blue_embed, self.bot)

            red_team_players = ""
            for idx, player in enumerate(red_team_db.players):
                red_team_players += f"{idx + 1} - <@{player.discord_id}>\n"
                await send_embed(player, red_embed, self.bot)

            embed = discord.Embed(
                title=f"Partidazuda ({match.id})",
                description="Em um embate do bem contra o mal, quem vencerá?",
                color=discord.Colour.blurple(),
            )
            embed.add_field(name="Time azul (Lado esquerdo)", value=blue_team_players)
            embed.add_field(name="Time vermelho (Lado direito)", value=red_team_players)

            await self.match_monitor.start_monitoring(players, match.id)
            await ctx.followup.send(
                embed=embed, view=ResultButtons(match.id, ctx.author.id, match_service=self.match_service)
            )

    @commands.slash_command(name="finalizar", description="Finaliza uma partida")
    async def finalize(
        self,
        ctx,
        match_id: Option(int, "Identificador da partida", required=True),
        result: Option(
            TeamSide,
            "Time vitorioso",
            required=True,
            choices=[
                OptionChoice("Azul", value=TeamSide.blue),
                OptionChoice("Vermelho", value=TeamSide.red),
            ],
        ),
    ):
        await ctx.response.defer()
        if not ctx.guild_id:
            await ctx.followup.send("Esse comando deve ser usado em um servidor")
            return

        if not ctx.user.guild_permissions.administrator:
            await ctx.followup.send("Somente admins podem usar esse comando")
            return

        with next(get_session()) as session:
            match = match_repo.get_by_id(session, match_id)

            if not match or match.result is not None:
                await ctx.followup.send("Partida já finalizada!")
                return

            self.match_service.finalize_match(session, match, result)

            await ctx.followup.send(
                f"Partida finalizada! Vitoria para o time {'azul' if result == TeamSide.blue else 'vermelho'}!"
            )

    @commands.slash_command(name="reverterpartida", description="Reverte uma partida já finalizada")
    async def revert(
        self,
        ctx,
        match_id: Option(int, "Identificador da partida", required=True),
    ):
        await ctx.response.defer()
        if not ctx.guild_id:
            await ctx.followup.send("Esse comando deve ser usado em um servidor")
            return

        if not ctx.user.guild_permissions.administrator:
            await ctx.followup.send("Somente admins podem usar esse comando")
            return

        with next(get_session()) as session:
            match = match_repo.get_by_id(session, match_id)

            if not match or match.result is None:
                await ctx.followup.send("Partida não finalizada!")
                return

            self.match_service.revert_match(session, match)

            await ctx.followup.send("Partida revertida!")


def setup(bot):
    bot.add_cog(MatchCog(bot))
