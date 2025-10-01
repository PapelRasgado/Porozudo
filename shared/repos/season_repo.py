from datetime import datetime

from sqlmodel import Session, select

from shared.model.database import Season


def get_last_season(session: Session) -> Season:
    return session.exec(select(Season).order_by(Season.start_date.desc())).first()


def create_season(session: Session, season: Season) -> Season:
    season_db = Season.model_validate(season)

    last_season = get_last_season(session)

    if last_season:
        last_season.end_date = datetime.now()
        session.add(last_season)

    session.add(season_db)
    session.commit()
    session.refresh(season_db)
    return season_db


def get_by_id(session, season) -> Season:
    return session.exec(select(Season).where(Season.id == season)).first()


def get_all_seasons(session):
    return session.exec(select(Season).order_by(Season.start_date.desc())).all()
