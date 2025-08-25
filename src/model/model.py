from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import Column, JSON
from sqlmodel import SQLModel, Field, Relationship

class TeamSide(str, Enum):
    blue = "blue"
    red = "red"

class Player(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    username: str = Field(index=True)
    discord_id: Optional[str] = Field(index=True)
    points : int = Field(default=1500)

class PlayerTeam(SQLModel, table=True):
    player_id: Optional[int] = Field(primary_key=True, foreign_key="player.id")
    team_id: Optional[int] = Field(primary_key=True, foreign_key="team.id")

class Match(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    create_at: datetime = Field(default_factory=datetime.now, nullable=False)
    mode : int = Field(ge=1, le=5)

    result : Optional[TeamSide]
    teams: List["Team"] = Relationship(back_populates="match")

class Team(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    side: TeamSide
    champions: List[str] = Field(sa_column=Column(JSON))
    team_rating : int

    players: List["Player"] = Relationship(link_model=PlayerTeam)
    match: "Match" = Relationship(back_populates="teams")


