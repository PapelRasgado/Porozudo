from datetime import datetime

from sqlmodel import Session, select

from src.model.database import Season


def get_last_season(session: Session) -> Season:
    return session.exec(select(Season).order_by(Season.start_date.desc())).first()


def create_season(session: Session, season: Season) -> Season:
    season_db = Season.model_validate(season)

    session.add(season_db)
    last_season = get_last_season(session)

    if last_season:
        last_season.end_date = datetime.now()
        session.add(last_season)

    session.commit()
    session.refresh(season_db)
    return season_db
