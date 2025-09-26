import logging

import discord

from src.model.database import TeamSide
from src.repos import config_repo, match_repo, player_repo
from src.repos.database import get_session
from src.service.match_service import MatchService
from src.utils.embed import create_active_players_embed

logger = logging.getLogger("c/views")


class TeamSelect(discord.ui.Select):
    """
    A dropdown menu to select players to be added to the active list.
    """

    async def callback(self, interaction: discord.Interaction):
        with next(get_session()) as session:
            players = player_repo.get_players_by_discord_ids(session, [str(user.id) for user in self.values])
            config_repo.add_to_pool(session, players)

            await interaction.response.send_message(
                content="Os jogadores foram adicionados à lista de ativos.",
                ephemeral=True,
                delete_after=5,
            )


class TeamSelectView(discord.ui.View):
    """
    A view that generates dropdown menus for selecting active players or fixed team members.
    """

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(
            TeamSelect(
                placeholder="Escolha os jogadores ativos!",
                min_values=1,
                max_values=10,
                select_type=discord.ComponentType.user_select,
            )
        )


class DeleteButton(discord.ui.Button):
    """
    A button to remove a specific player from the active players list.
    """

    def __init__(self, player_id, label):
        super().__init__(label=label, custom_id=str(player_id), style=discord.ButtonStyle.red)
        self.player_id = player_id

    async def callback(self, interaction: discord.Interaction):
        with next(get_session()) as session:
            config_repo.remove_from_pool(session, int(self.player_id))
            players = config_repo.get_pool_players(session)
            embed = create_active_players_embed(players)

            view = DeleteButtons(players)

            await interaction.message.edit(embed=embed, view=view)
            await interaction.response.send_message("Jogador removido!", ephemeral=True)


class DeleteButtons(discord.ui.View):
    """
    A view that contains buttons to remove active players.
    """

    def __init__(self, players):
        super().__init__(timeout=None)
        for idx, player in enumerate(players):
            self.add_item(DeleteButton(player_id=player.id, label=f"Jogador {idx + 1}"))


class ResultButtons(discord.ui.View):
    """
    A view to set the match result, with buttons for each team.
    """

    def __init__(self, match_id, author_id, match_service: MatchService):
        super().__init__(timeout=None)
        self.match_id = match_id
        self.author_id = author_id
        self.match_service = match_service

    @discord.ui.button(label="Vitória para o time azul", style=discord.ButtonStyle.blurple)
    async def blue_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self._handle_result(interaction, TeamSide.blue)

    @discord.ui.button(label="Vitória para o time vermelho", style=discord.ButtonStyle.red)
    async def red_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self._handle_result(interaction, TeamSide.red)

    async def _handle_result(self, interaction: discord.Interaction, result: TeamSide):
        """
        Handle match result submission based on the user's interaction.
        """
        if interaction.user.id != self.author_id and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "Somente a pessoa que usou o comando pode definir os ganhadores!",
                ephemeral=True,
            )
            return

        with next(get_session()) as session:
            match = match_repo.get_by_id(session, self.match_id)
            if not match or match.result is not None:
                return

            match.result = result

            self.match_service.finalize_match(session, match, result)

            embeds = interaction.message.embeds

            if len(embeds) == 1:
                embed = embeds[0]
                embed.description = f"Vitoria para o time {'azul' if result == TeamSide.blue else 'vermelho'}! (Definido por {interaction.user.mention})"

                await interaction.message.edit(embed=embed, view=None)
            else:
                await interaction.message.edit(view=None)
                await interaction.message.reply(
                    f"Vitoria para o time {'azul' if result == TeamSide.blue else 'vermelho'}! (Definido por {interaction.user.mention})"
                )
