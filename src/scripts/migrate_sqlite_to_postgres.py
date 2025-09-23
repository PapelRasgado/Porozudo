import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlmodel import Session, select

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.model.database import Player, Season, Match, Team, PlayerTeam, PlayerEloHistory, PlayerMatchChampion

load_dotenv()

TABLES_IN_ORDER = [Player, Season, Match, Team, PlayerTeam, PlayerEloHistory, PlayerMatchChampion]


def run_data_migration():
    print("Starting data migration from SQLite to Postgres...")

    sqlite_url = os.getenv("OLD_SQLITE_URL")
    postgres_url = os.getenv("DATABASE_URL")

    if not sqlite_url or not postgres_url:
        raise ValueError("Database URLs not found on .env")

    sqlite_engine = create_engine(sqlite_url)
    postgres_engine = create_engine(postgres_url)

    with Session(sqlite_engine) as sqlite_session, Session(postgres_engine) as postgres_session:
        for model in TABLES_IN_ORDER:
            table_name = model.__tablename__
            print(f"Migrating data from table: {table_name}...")

            items_from_sqlite = sqlite_session.exec(select(model)).all()

            for item in items_from_sqlite:
                new_item = model.model_validate(item.model_dump())
                postgres_session.add(new_item)

            postgres_session.commit()
            print(f"  {len(items_from_sqlite)} records migrated from table {table_name}.")

    print("Data migration complete.!")


if __name__ == "__main__":
    run_data_migration()