import logging
from typing import Optional

import aiohttp
from dotenv import load_dotenv
from pydantic import BaseModel

from src.model.riot import AccountSchema, ActiveGameSchema

load_dotenv()

logger = logging.getLogger("c/riot_client")


class RiotAPIClient:
    def __init__(self, api_key: str, session: aiohttp.ClientSession):
        self._session: aiohttp.ClientSession = session
        self._headers = {"X-Riot-Token": api_key}
        self._base_url_br = "https://br1.api.riotgames.com"
        self._base_url_americas = "https://americas.api.riotgames.com"

    async def _request(self, url: str, response_schema: Optional[BaseModel] = None):
        if not self._session:
            raise RuntimeError("The session has been closed.")

        try:
            async with self._session.get(url, headers=self._headers, timeout=10.0) as response:
                response.raise_for_status()
                data = await response.json()

                if response_schema:
                    return response_schema.model_validate(data)

                return data
        except aiohttp.ClientResponseError as e:
            logger.error(f"Error on Riot API: {e.status} - {e.message} - URL: {url}")
            raise

    async def get_puuid_by_riot_name(self, game_name: str, tag_line: str) -> AccountSchema:
        url = f"{self._base_url_americas}/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        return await self._request(url, response_schema=AccountSchema)

    async def get_active_game_by_puuid(self, puuid: str) -> ActiveGameSchema:
        url = f"{self._base_url_br}/lol/spectator/v5/active-games/by-summoner/{puuid}"
        return await self._request(url, response_schema=ActiveGameSchema)
