from fastapi import FastAPI

from api.routers import player

app = FastAPI()

app.include_router(player.router)
