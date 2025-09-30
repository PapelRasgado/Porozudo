from sqlmodel import Session

from shared.model.database import PlayerEloHistory, PlayerSeasonFinalElo


def create_history(session: Session, history: PlayerEloHistory) -> PlayerEloHistory:
    history_db = PlayerEloHistory.model_validate(history)

    session.add(history_db)
    session.commit()
    session.refresh(history_db)
    return history_db


def create_season_history(session: Session, season_elo: PlayerSeasonFinalElo) -> PlayerSeasonFinalElo:
    season_elo_db = PlayerSeasonFinalElo.model_validate(season_elo)

    session.add(season_elo_db)
    session.commit()
    session.refresh(season_elo_db)
    return season_elo_db
