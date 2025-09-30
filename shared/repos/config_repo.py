from typing import List

from sqlmodel import Session, delete, select

from shared.model.database import ActivePlayer, Player


def add_to_pool(session: Session, players: List[Player]):
    actual_pool = set(get_pool_players(session))
    active_players = [ActivePlayer(player_id=player.id) for player in players if player not in actual_pool]
    session.add_all(active_players)
    session.commit()


def remove_from_pool(session: Session, player_id: int):
    active_player = session.exec(select(ActivePlayer).where(ActivePlayer.player_id == player_id)).first()
    if active_player:
        session.delete(active_player)
        session.commit()


def get_pool_players(session: Session) -> List[Player]:
    query = select(Player).join(ActivePlayer, Player.id == ActivePlayer.player_id)

    return session.exec(query).all()


def clear_player_pool(session: Session):
    statement = delete(ActivePlayer)

    session.exec(statement)
    session.commit()
