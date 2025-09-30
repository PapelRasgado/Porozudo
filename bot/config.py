import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TOKEN")
if not BOT_TOKEN:
    raise ValueError("The bot token is not set on environment variables")

RIOT_API_KEY = os.getenv("RIOT_API_KEY")
if not RIOT_API_KEY:
    raise ValueError("The riot API key is not set on environment variables")

LAVALINK_URL = os.getenv("LAVALINK_URL", "127.0.0.1")
LAVALINK_PORT = int(os.getenv("LAVALINK_PORT", 2333))
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD", "youshallnotpass")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./resources/database.db")
