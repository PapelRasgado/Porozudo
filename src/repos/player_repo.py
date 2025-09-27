from typing import List, Optional, Sequence

from sqlmodel import Session, and_, select

from src.model.database import Player, PlayerEloHistory, PlayerTeam, Team


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
    return session.exec(select(Player).join(PlayerEloHistory).distinct().order_by(Player.points.desc())).all()


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
