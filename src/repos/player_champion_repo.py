from sqlmodel import Session

from src.model.database import PlayerMatchChampion


def create_player_champion(session: Session, player_champion: PlayerMatchChampion) -> PlayerMatchChampion:
    player_champion_db = PlayerMatchChampion.model_validate(player_champion)

    session.add(player_champion_db)
    session.commit()
    session.refresh(player_champion_db)
    return player_champion_db
