import asyncio
import datetime
import logging
import os

import wavelink
from discord import Activity, ActivityType
from discord.bot import Bot
from discord.ext import tasks
from dotenv import load_dotenv


# from index_pdf import process_pdfs
from src.commands.config import register_config_commands
from src.commands.match import register_match_commands
from src.commands.music import register_music_commands
from src.commands.stats import register_stats_commands
from src.repos.champions_repo import ImageDict

# from commands.rpg import register_rpg_commands
from src.repos.database import create_db_and_tables

logging.basicConfig(format="%(levelname)s %(name)s %(asctime)s: %(message)s", level=logging.INFO)
logger = logging.getLogger("main")

load_dotenv()
bot = Bot()

champion_data = ImageDict()

register_stats_commands(bot)
register_match_commands(bot, champion_data)
register_config_commands(bot)
register_music_commands(bot)
# register_rpg_commands(bot)
# process_pdfs()


async def connect_nodes():
    await bot.wait_until_ready()

    LAVALINK_URL = os.getenv("LAVALINK_URL")
    LAVALINK_PORT = os.getenv("LAVALINK_PORT")
    LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD")

    nodes = [
        wavelink.Node(
            identifier="Node",
            uri=f"http://{LAVALINK_URL}:{LAVALINK_PORT}",
            password=LAVALINK_PASSWORD,
            inactive_player_timeout=60,
            inactive_channel_tokens=1,
        )
    ]

    await wavelink.Pool.connect(
        nodes=nodes,
        client=bot,
    )


@tasks.loop(hours=24)
async def daily_champion_update():
    logger.info("Updating champion data")
    try:
        champion_data.update_data()
        logger.info("Champion data updated.")
    except Exception as e:
        logger.error(f"Failed to update champion data: {e}")


daily_champion_update.change_interval(time=datetime.time(hour=6, minute=0))


@bot.event
async def on_ready():
    logger.info(f"{bot.user} tá on pai!")
    await bot.change_presence(
        activity=Activity(type=ActivityType.custom, name="custom", state="Fraudando as runas....")
    )
    await connect_nodes()


def main():
    TOKEN = os.getenv("TOKEN")
    if not TOKEN:
        raise EnvironmentError("TOKEN is not set in the environment variables.")

    bot.run(TOKEN)


if __name__ == "__main__":
    create_db_and_tables()
    asyncio.run(main())
