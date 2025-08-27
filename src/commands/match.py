import logging

import discord
from discord.bot import Bot
from discord.commands import Option

from src.model.database import Match, Player
from src.repos import config_repo, match_repo, player_repo, season_repo
from src.repos.champions_repo import ImageDict
from src.repos.database import get_session
from src.team_generator.generator import generate_teams
from src.ui.views import DeleteButtons, ResultButtons, TeamSelectView
from src.utils.embed import create_active_players_embed, create_champion_embed

logging.basicConfig(format="%(levelname)s %(name)s %(asctime)s: %(message)s", level=logging.INFO)
logger = logging.getLogger("c/match")


def register_match_commands(bot: Bot, champions_data: ImageDict):
    @bot.slash_command(name="adicionar", description="Adiciona jogadores a lista de ativos")
    async def add_active_players(ctx: discord.ApplicationContext):
        await ctx.response.defer(ephemeral=True)
        await ctx.followup.send("Monta o time!", view=TeamSelectView())

    @bot.slash_command(
        name="canal", description="Adiciona os jogadores que estão em um determinado canal a lista de ativos"
    )
    async def add_channel_active_players(ctx: discord.ApplicationContext):
        await ctx.response.defer(ephemeral=True)
        with next(get_session()) as session:
            member = ctx.guild.get_member(ctx.user.id)
            voice = member.voice

            if not voice:
                await ctx.followup.send("É necessário estar conectado a um canal de voz para executar esse comando!")
                return

            players = player_repo.get_players_by_discord_ids(session, list(voice.channel.voice_states))
            config_repo.add_to_pool(session, players)

            await ctx.followup.send(f"Os jogadores do canal {voice.channel.name} foram adicionados a lista de ativos!")

    @bot.slash_command(name="limpar", description="Apaga todos os jogadores da lista de ativos")
    async def clear_active_players(ctx):
        await ctx.response.defer(ephemeral=True)
        with next(get_session()) as session:
            config_repo.clear_player_pool(session)
            await ctx.followup.send("A lista de jogadores ativos foi esvaziada!")

    @bot.slash_command(name="ativos", description="Mostra os jogadores ativos")
    async def list_active_players(ctx):
        await ctx.response.defer()
        with next(get_session()) as session:
            players = config_repo.get_pool_players(session)
            embed = create_active_players_embed(players)
            await ctx.followup.send(embed=embed, view=DeleteButtons(players))

    async def send_embed(player_info, embed):
        player_discord = await bot.fetch_user(player_info.discord_id)

        try:
            embed["file"].seek(0)
            file = discord.File(fp=embed["file"], filename="image.png")

            await player_discord.send(file=file, embed=embed["embed"])
        except Exception as e:
            logger.warning(f"Failed to send message to user {player_discord.name}, cause: {e}")

    @bot.slash_command(name="sortear", description="Sortea os times e campeões")
    async def sort_active_players(
        ctx, choices_number: Option(int, "Quantidade de campeões", name="opções", default=0, min_value=1, max_value=10)
    ):
        await ctx.response.defer()
        with next(get_session()) as session:
            players = config_repo.get_pool_players(session)
            teams = generate_teams(players, list(champions_data), choices_number)
            season = season_repo.get_last_season(session)
            match = match_repo.create(session, Match(teams=teams, mode=len(teams[0].players), season=season))

            blue_team_db = teams[0] if teams[0].side == "blue" else teams[1]
            red_team_db = teams[1] if teams[1].side == "red" else teams[0]

            blue_embed = create_champion_embed(blue_team_db.champions, champions_data, discord.Colour.blue(), 1)
            red_embed = create_champion_embed(red_team_db.champions, champions_data, discord.Colour.red(), 2)

            blue_team_players = ""
            for idx, player in enumerate(blue_team_db.players):
                blue_team_players += f"{idx + 1} - <@{player.discord_id}>\n"
                await send_embed(player, blue_embed)

            red_team_players = ""
            for idx, player in enumerate(red_team_db.players):
                red_team_players += f"{idx + 1} - <@{player.discord_id}>\n"
                await send_embed(player, red_embed)

            embed = discord.Embed(
                title="Partidazuda",
                description="Em um embate do bem contra o mal, quem vencerá?",
                color=discord.Colour.blurple(),
            )
            embed.add_field(name="Time azul (Lado esquerdo)", value=blue_team_players)
            embed.add_field(name="Time vermelho (Lado direito)", value=red_team_players)
            await ctx.followup.send(embed=embed, view=ResultButtons(match.id, ctx.author.id))

    @bot.slash_command(name="registrar", description="Adicionar jogador")
    async def register_new_player(ctx, nome: str, user: discord.User):
        await ctx.response.defer(ephemeral=True)
        with next(get_session()) as session:
            player_repo.create_player(session, Player(username=nome, discord_id=str(user.id)))
            await ctx.followup.send(f"{nome} registrado com sucesso.")
