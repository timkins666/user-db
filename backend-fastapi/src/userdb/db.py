"""initialises postgres db"""

import logging
import os
from typing import Annotated
from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine

# pylint: disable=unused-import
from userdb.models.user import User

_logger = logging.getLogger(__name__)


def db_url():
    """get postgres connection url with dev server defaults"""
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgresP")
    host = os.getenv("POSTGRES_HOST", "localhost:5432")
    db_name = os.getenv("POSTGRES_DB", "userdb")
    return f"postgresql://{user}:{password}@{host}/{db_name}"


engine = create_engine(db_url())


def init_db() -> None:
    """initialize database with configured tables"""
    _logger.info("initialising database and tables")

    # wouldn't do this in real life obvs
    if os.getenv("REFRESH_DB") == "true":
        _logger.warning("REFRESH_DB set - deleting all users")
        SQLModel.metadata.drop_all(engine)

    SQLModel.metadata.create_all(engine)


def get_session():
    """get db session"""
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
