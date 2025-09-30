from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, create_engine

from api.config.config import DATABASE_URL

engine = create_engine(DATABASE_URL)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
