from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class PlayerPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    puuid: Optional[str]
    username: str
    discord_id: Optional[str]
    points: int


class PaginatedRanking(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[PlayerPublic]
