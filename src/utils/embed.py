import io
from typing import List

import discord
from PIL import Image, ImageDraw

from src.model.database import Player
from src.repos.champions_repo import ImageDict


def create_image_from_champions(champions_list: list[str], data: ImageDict) -> io.BytesIO:
    max_width, max_height = 680, 281
    new_im = Image.new("RGBA", (max_width, max_height), (255, 0, 0, 0))
    new_im_draw = ImageDraw.Draw(new_im)

    x_offset = 10
    y_offset = 10
    for idx, _id in enumerate(champions_list):
        champion_data = data[_id]
        img = Image.open(io.BytesIO(champion_data["image"]))
        new_im.paste(img, (x_offset, y_offset))

        new_im_draw.text(
            (x_offset + 5, y_offset), str(idx + 1), font_size=30, fill="white", stroke_width=2, stroke_fill="black"
        )

        x_offset += 133
        if x_offset >= max_width - 10:
            x_offset = 10
            y_offset += 133

    image_buffer = io.BytesIO()
    new_im.save(image_buffer, format="PNG")
    image_buffer.seek(0)
    return image_buffer


def create_champion_embed(
    champions_list: list[str], data: ImageDict, colour: discord.Colour, team: int, players: List[Player]
) -> dict:
    if team == 1:
        embed_description = (
            "Você está no time Azul :blue_circle:, localizado no lado esquerdo :arrow_left: da "
            "personalizada. <a:calabreso:1320528277873365012>\n\n**Campeões:**\n```yaml\n"
        )
    else:
        embed_description = (
            "Você está no time Vermelho :red_circle:, localizado no lado direito :arrow_right: da "
            "personalizada. <a:calabreso:1320528277873365012>\n\n**Campeões:**\n```haskell\n"
        )

    embed_description += "\n".join([data[_id]["name"] for _id in champions_list]) + "\n```"

    embed_description += "\n**Time:**\n```\n" + "\n".join([player.username for player in players]) + "\n```"

    image_buffer = create_image_from_champions(champions_list, data)
    embed = discord.Embed(
        title="Só os bonecudos",
        description=embed_description,
        color=colour,
    )
    embed.set_image(url="attachment://image.png")

    return {"embed": embed, "file": image_buffer}


def create_active_players_embed(players):
    """
    Create an embed displaying the list of active players.
    """
    embed = discord.Embed(title="Jogadores ativos", color=discord.Colour.blurple())

    for idx, player in enumerate(players):
        embed.add_field(
            name=f"Jogador {idx + 1}",
            value=f"<@{player.discord_id}>",
            inline=True,
        )
    return embed


def create_match_history_embed(matches, player):
    """
    Create an embed displaying the last matches of player.
    """
    embed = discord.Embed(title=f"Últimas Partidas de {player.username}", color=discord.Colour.blurple())

    if not matches:
        embed.description = "Este jogador não possui partidas finalizadas."
        return embed

    for match in matches:
        match_date = match.created_at.strftime("%d/%m/%Y %H:%M")
        mode = match.mode
        player_team = next((team for team in match.teams if player in team.players), None)

        if player_team and player_team.side == match.result:
            result_text = "Vitória"
        else:
            result_text = "Derrota"

        embed.add_field(name=f"{match_date} - {mode}x{mode}", value=result_text, inline=False)
    return embed
