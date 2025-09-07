from typing import List

from pydantic import BaseModel, Field


class AccountSchema(BaseModel):
    puuid: str
    game_name: str = Field(alias="gameName")
    tag_line: str = Field(alias="tagLine")


class SpectatorParticipantSchema(BaseModel):
    puuid: str
    champion_id: str = Field(alias="championId")


class ActiveGameSchema(BaseModel):
    game_id: int = Field(alias="gameId")
    participants: List[SpectatorParticipantSchema]
