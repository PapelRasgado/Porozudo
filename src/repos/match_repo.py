from typing import List

from sqlmodel import Session, select

from src.model.database import Match, Player, PlayerTeam, Team


def get_by_id(session: Session, match_id: int) -> Match:
    return session.exec(select(Match).where(Match.id == match_id)).first()


def get_all_by_player(session: Session, player_id: int, limit: int) -> List[Match]:
    query = (
        select(Match)
        .join(Team)
        .join(PlayerTeam)
        .join(Player)
        .where(Player.id == player_id)
        .order_by(Match.created_at.desc())
        .limit(limit)
    )

    return session.exec(query).all()


def get_all(session: Session) -> List[Match]:
    return session.exec(select(Match)).all()


def create(session: Session, match: Match) -> Match:
    match_db = Match.model_validate(match)

    session.add(match_db)
    session.commit()
    session.refresh(match_db)
    return match_db


def update(session: Session, match: Match) -> Match:
    session.add(match)
    session.commit()
    session.refresh(match)

    return match
