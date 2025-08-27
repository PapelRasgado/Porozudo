from sqlmodel import Session

from src.model.database import PlayerEloHistory


def create_history(session: Session, history: PlayerEloHistory) -> PlayerEloHistory:
    history_db = PlayerEloHistory.model_validate(history)

    session.add(history_db)
    session.commit()
    session.refresh(history_db)
    return history_db
