from typing import List, Optional, Sequence, Tuple

from sqlalchemy import func
from sqlmodel import Session, and_, select

from shared.model.database import Match, Player, PlayerEloHistory, PlayerTeam, Season, Team


def get_all_players(session) -> List[Player]:
    return session.exec(select(Player)).all()


def get_player_by_discord(session: Session, discord_id: str) -> Optional[Player]:
    return session.exec(select(Player).where(Player.discord_id == discord_id)).first()


def get_player_by_id(session: Session, player_id: int) -> Player:
    return session.exec(select(Player).where(Player.id == player_id)).first()


def get_players_by_ids(session: Session, ids: List[int]) -> Player:
    return session.exec(select(Player).where(Player.id.in_(ids))).all()


def get_players_by_discord_ids(session: Session, discord_ids: List[str]) -> List[Player]:
    return session.exec(select(Player).where(Player.discord_id.in_(discord_ids))).all()


def get_all_players_ranked(session: Session) -> List[Player]:
    last_season_subquery = select(Season.id).order_by(Season.start_date.desc()).limit(1)

    statement = (
        select(Player)
        .distinct()
        .join(PlayerTeam)
        .join(Team)
        .join(Match)
        .where(and_(Match.season_id.in_(last_season_subquery), Match.result.is_not(None)))
        .order_by(Player.points.desc())
    )

    players = session.exec(statement).all()
    return players


def get_all_players_ranked_paginated(session: Session, limit: int, offset: int) -> Tuple[List[Player], int]:
    base_query = select(Player).join(PlayerEloHistory).distinct()

    count_statement = select(func.count(base_query.c.id))
    total_players = session.exec(count_statement).one()

    paginated_statement = base_query.order_by(Player.points.desc()).offset(offset).limit(limit)

    players_on_page = session.exec(paginated_statement).all()

    return players_on_page, total_players


def get_all_players_by_match(session: Session, match_id: int) -> Sequence[str]:
    return session.exec(
        select(Player.puuid)
        .join(PlayerTeam)
        .join(Team)
        .where(and_(Team.match_id == match_id, Player.puuid.is_not(None)))
    ).all()


def create_player(session: Session, player: Player) -> Player:
    player_db = Player.model_validate(player)

    session.add(player_db)
    session.commit()
    session.refresh(player_db)
    return player_db


def update_player(session: Session, player: Player) -> Player:
    session.add(player)
    session.commit()
    session.refresh(player)

    return player
