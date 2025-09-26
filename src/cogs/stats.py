import logging

from discord import Cog, Color, Embed, User
from discord.commands import ApplicationContext, Option, OptionChoice
from discord.ext import commands

from src.main import PorozudoBot
from src.repos import match_repo, player_repo, stat_repo
from src.repos.database import get_session
from src.utils.embed import create_match_history_embed

logger = logging.getLogger("c/stats")


class StatsCog(Cog):
    def __init__(self, bot: "PorozudoBot"):
        self.bot = bot

    @commands.slash_command(name="vitorias", description="Quantifica as vitorias de cada jogador")
    async def victories(
        self,
        ctx: ApplicationContext,
        mode: Option(
            int,
            "Escolha o modo de jogo",
            default=0,
            choices=[
                OptionChoice("Todos", value=0),
                OptionChoice("5X5", value=5),
                OptionChoice("4X4", value=4),
                OptionChoice("3X3", value=3),
            ],
        ),
    ):
        await ctx.response.defer(ephemeral=True)
        with next(get_session()) as session:
            stats = stat_repo.get_players_stat(session, mode)

            result_list = sorted(stats.values(), key=lambda x: x["wins"], reverse=True)

            result_strings = [
                f"{rank + 1}º - <@{player['discord_id']}> - {player['wins']} vitorias"
                for rank, player in enumerate(result_list)
            ]

            embed = Embed(
                title=f"Rankzudo {'Geral' if not mode else f'{mode}X{mode}'}", description="\n".join(result_strings)
            )

            await ctx.followup.send(embed=embed)

    @commands.slash_command(name="winrate", description="Quantifica o winrate de cada jogador")
    async def winrate(
        self,
        ctx: ApplicationContext,
        mode: Option(
            int,
            "Escolha o modo de jogo",
            name="modo",
            default=0,
            choices=[
                OptionChoice("Todos", value=0),
                OptionChoice("5X5", value=5),
                OptionChoice("4X4", value=4),
                OptionChoice("3X3", value=3),
            ],
        ),
        minimal: Option(int, "Quantidade minima de jogos", name="corte", default=10, min_value=1, max_value=30),
    ):
        await ctx.response.defer(ephemeral=True)
        with next(get_session()) as session:
            stats = stat_repo.get_players_stat(session, mode)

            filtered_stats = {player_id: data for player_id, data in stats.items() if data["games"] >= minimal}

            result_list = sorted(filtered_stats.values(), key=lambda x: x["winrate"], reverse=True)

            result_strings = [
                f"{rank + 1}º - <@{player['discord_id']}> - {player['winrate']:.2f}% | {player['games']} jogos"
                for rank, player in enumerate(result_list)
            ]

            description = (
                "\n".join(result_strings)
                if len(result_strings) > 1
                else "Não foi encontrado nenhum dado compatível com os parâmetros selecionados."
            )

            embed = Embed(
                title=f"Rankzudo {'Geral' if not mode else f'{mode}X{mode}'} - Mínimo de {minimal} jogos",
                description=description,
            )

            await ctx.followup.send(embed=embed)

    @commands.slash_command(name="historico", description="Exibe o historico de partidas de um jogador")
    async def match_history(
        self,
        ctx: ApplicationContext,
        user: Option(User, "Usuário a ser consultado", name="usuário", required=False),
        limit: Option(int, "Limite de partidas", name="limite", default=10, min_value=1, max_value=50),
    ):
        await ctx.response.defer(ephemeral=True)
        with next(get_session()) as session:
            player = player_repo.get_player_by_discord(session, str(user.id if user else ctx.author.id))

            matches = match_repo.get_all_finished_by_player(session, player.id, limit)

            embed = create_match_history_embed(matches, player)

            await ctx.followup.send(embed=embed)

    @commands.slash_command(name="elo", description="Mostra o ranking de Elo dos jogadores.")
    async def ranking(self, ctx: ApplicationContext):
        await ctx.response.defer(ephemeral=True)

        with next(get_session()) as session:
            all_ranked_players = player_repo.get_all_players_ranked(session)

        if not all_ranked_players:
            await ctx.followup.send("Ainda não há jogadores no ranking.")
            return

        author_id = str(ctx.user.id)
        author_rank_data = None
        for rank, player in enumerate(all_ranked_players, start=1):
            if player.discord_id == author_id:
                author_rank_data = {"rank": rank, "player": player}
                break

        top_players = all_ranked_players[:10]

        embed = Embed(title="🏆 Ranking de Elo", color=Color.gold())

        top_description = []
        rank_emojis = {1: "🥇", 2: "🥈", 3: "🥉"}

        for rank, player in enumerate(top_players, start=1):
            emoji = rank_emojis.get(rank, f"**{rank}.**")
            top_description.append(f"{emoji} <@{player.discord_id}> - `{player.points}` Pontos")

        embed.description = "\n".join(top_description)

        if author_rank_data and author_rank_data["rank"] > 10:
            author = author_rank_data["player"]
            embed.add_field(
                name="Sua Posição",
                value=f"**{author_rank_data['rank']}.** <@{author.discord_id}> - `{author.points}` Pontos",
                inline=False,
            )

        await ctx.followup.send(embed=embed)


def setup(bot):
    try:
        bot.add_cog(StatsCog(bot))
    except Exception as e:
        logger.info(e)
