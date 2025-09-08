import json
import logging
import os
from queue import Empty, Queue
from threading import Thread

import requests

logger = logging.getLogger("champions")

BASE_API_URL = "https://ddragon.leagueoflegends.com"
CACHE_FILE = "./resources/champion_cache.json"


def download_champion_image(version, name):
    url = f"{BASE_API_URL}/cdn/{version}/img/champion/{name}.png"
    response = requests.get(url)
    return response.content


def get_last_league_version():
    url = f"{BASE_API_URL}/api/versions.json"

    response = requests.get(url)

    if response.status_code == 200:
        return response.json()[0]
    else:
        logger.error("Error getting last league version: %s", response.text)
        raise Exception("Error getting last league version")


def download_champion_data(version):
    url = f"{BASE_API_URL}/cdn/{version}/data/pt_BR/champion.json"

    response = requests.get(url)

    logger.info("Downloading champions list")
    if response.status_code == 200:
        champions = response.json()["data"]
        champions_data = {}
        q = Queue()

        def __fetch_champion():
            finished = False
            while not finished:
                try:
                    champion_name = q.get(block=False)
                    logger.info(f"Downloading champion {champion_name}")
                    image = download_champion_image(version, champion_name)
                    champions_data[champions[champion_name]["key"]] = {
                        "name": champions[champion_name]["name"],
                        "image": image,
                        "id": champions[champion_name]["key"],
                    }
                    q.task_done()
                except Empty:
                    finished = True

        for champion in champions:
            q.put(champion)

        for i in range(10):
            t = Thread(target=__fetch_champion, daemon=True)
            t.start()

        q.join()
        logger.info("Download finished")

        return champions_data

    else:
        logger.error("Error getting champions list: %s", response.text)
        raise Exception("Error getting champions list")


def get_champions():
    latest_version = get_last_league_version()

    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            cache = json.load(f)
            cached_version = cache.get("version")

            if cached_version == latest_version:
                logger.info("Using cached champions data.")
                champions_data = {
                    _id: {"name": d["name"], "image": bytes.fromhex(d["image"]), "id": d["id"]}
                    for _id, d in cache["champions"].items()
                }
                return champions_data

    logger.info(f"New version found: {latest_version}. Downloading new champion data...")
    champions_data = download_champion_data(latest_version)

    with open(CACHE_FILE, "w") as f:
        cache_data = {
            "version": latest_version,
            "champions": {
                _id: {"name": d["name"], "image": d["image"].hex(), "id": d["id"]} for _id, d in champions_data.items()
            },
        }
        json.dump(cache_data, f, indent=4)

    return {
        _id: {"name": d["name"], "image": bytes.fromhex(d["image"].hex()), "id": d["id"]}
        for _id, d in champions_data.items()
    }


class ImageDict(dict):
    def __init__(self):
        super().__init__()
        self.update_data()

    def update_data(self):
        self.update(get_champions())
