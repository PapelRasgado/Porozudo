import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Optional

import aiohttp

from src.client.riot_client import RiotAPIClient
from src.repos import player_repo
from src.repos.database import get_session
from src.service.match_service import MatchService

logger = logging.getLogger("c/champions_m")


class ActiveMatchMonitor:

    def __init__(self, riot_client: RiotAPIClient, match_service: MatchService):
        self._match_id = None
        self._riot_client = riot_client
        self.match_service = match_service
        self._current_task: Optional[asyncio.Task] = None

    async def start_monitoring(self, match_id: int) -> None:
        await self.stop_monitoring()

        logger.info(f"Starting monitoring for match {match_id}.")
        self._match_id = match_id
        self._current_task = asyncio.create_task(self._monitor_loop())

    async def stop_monitoring(self):
        if self._current_task and not self._current_task.done():
            logger.info("Stoping previously started monitoring.")
            self._current_task.cancel()
            try:
                await self._current_task
            except asyncio.CancelledError:
                logger.info("Previous task was successfully cancelled.")
        self._current_task = None

    async def _monitor_loop(self):
        with next(get_session()) as session:
            start_time = datetime.now()
            timeout = timedelta(minutes=20)

            tracked_puuids = player_repo.get_all_players_by_match(session, self._match_id)

            try:
                while datetime.now() - start_time < timeout:
                    logger.info("Monitor: Checking active match...")

                    player_to_check = random.choice(list(tracked_puuids))

                    try:
                        active_game = await self._riot_client.get_active_game_by_puuid(player_to_check.puuid)
                        participants_in_game = {p.puuid for p in active_game.participants}

                        if tracked_puuids.issubset(participants_in_game):
                            logger.info(f"Monitor: Valid match found! Riot Match ID: {active_game.game_id}")
                            self.match_service.register_match_champions(self._match_id, active_game)
                            break

                    except aiohttp.ClientResponseError as e:
                        if e.status != 404:
                            logger.error(f"Monitor: Unexpected API error: {e.status}")

                    await asyncio.sleep(30)

            except asyncio.CancelledError:
                logger.info("Monitor: Loop cancelled.")
            finally:
                logger.info("Monitor: Ending monitoring loop.")
                self._current_task = None
