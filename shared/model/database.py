from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel


class TeamSide(str, Enum):
    blue = "blue"
    red = "red"


class Player(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    puuid: Optional[str] = Field(default=None, index=True)
    username: str = Field(index=True)
    discord_id: Optional[str] = Field(index=True)
    points: int = Field(default=1500)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not isinstance(other, Player):
            return NotImplemented
        return self.id == other.id


class PlayerTeam(SQLModel, table=True):
    player_id: Optional[int] = Field(primary_key=True, foreign_key="player.id")
    team_id: Optional[int] = Field(primary_key=True, foreign_key="team.id")


class Match(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    created_at: datetime = Field(default_factory=datetime.now, nullable=False)
    mode: int = Field(ge=1, le=5)
    season_id: Optional[int] = Field(default=None, foreign_key="season.id")
    champions_registered: bool = Field(default=False, nullable=False)

    season: "Season" = Relationship(back_populates="matches")
    result: Optional[TeamSide]
    teams: List["Team"] = Relationship(back_populates="match")
    elo_history: List["PlayerEloHistory"] = Relationship()


class Team(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    side: TeamSide
    champions: List[str] = Field(sa_column=Column(JSON))
    team_rating: float
    match_id: Optional[int] = Field(default=None, foreign_key="match.id")

    players: List["Player"] = Relationship(link_model=PlayerTeam)
    match: "Match" = Relationship(back_populates="teams")


class ActivePlayer(SQLModel, table=True):
    player_id: int = Field(primary_key=True, foreign_key="player.id")


class Season(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    start_date: datetime = Field(default_factory=datetime.now, nullable=False)
    end_date: Optional[datetime] = Field(nullable=True)

    matches: List["Match"] = Relationship(back_populates="season")


class PlayerEloHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    player_id: int = Field(foreign_key="player.id", index=True)
    match_id: Optional[int] = Field(default=None, foreign_key="match.id", index=True)
    is_reverted: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(default_factory=datetime.now, nullable=False)
    points_before: int
    points_after: int
    change: Optional[int]


class PlayerMatchChampion(SQLModel, table=True):
    player_id: int = Field(primary_key=True, foreign_key="player.id", index=True)
    match_id: int = Field(primary_key=True, foreign_key="match.id", index=True)
    champion_id: str = Field(index=True)


class PlayerSeasonFinalElo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    player_id: int = Field(foreign_key="player.id", index=True)
    season_id: int = Field(foreign_key="season.id", index=True)
    points: int
