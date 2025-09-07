import asyncio
import logging
import os

import aiohttp
import discord

from src.client.riot_client import RiotAPIClient
from src.config import BOT_TOKEN, RIOT_API_KEY
from src.repos.champions_repo import ImageDict

logging.basicConfig(format="%(levelname)s %(name)s %(asctime)s: %(message)s", level=logging.INFO)
logger = logging.getLogger("main")


class PorozudoBot(discord.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.http_session = aiohttp.ClientSession()
        self.riot_client = RiotAPIClient(api_key=RIOT_API_KEY, session=self.http_session)
        self.champion_data = ImageDict()

    async def close(self):
        await super().close()
        if self.http_session:
            await self.http_session.close()


async def main():
    bot = PorozudoBot(intents=discord.Intents.default())

    for filename in os.listdir("./src/cogs"):
        if filename.endswith(".py"):
            try:
                bot.load_extension(f"src.cogs.{filename[:-3]}")
                logger.info(f"Cog '{filename[:-3]}' successfully loaded.")
            except Exception as e:
                logger.info(f"Failed to load cog '{filename[:-3]}': {e}")

    await bot.start(BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
