"""common test setup"""

from fastapi.testclient import TestClient
import pytest
from sqlmodel import Session, SQLModel, create_engine, delete
from sqlmodel.pool import StaticPool

from userdb.db import get_session
from userdb.main import app
from userdb.models.user import User


@pytest.fixture(name="app", scope="session")
def _app(session):
    """
    FastAPI TestClient app fixture.
    Overrides `get_session` to use sqlite db.
    """

    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture(name="session", scope="session")
def _session():
    """return sqlite test db session"""

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


@pytest.fixture(autouse=True)
def pre_cleanup(session: Session):
    """delete any users in the db before each test"""
    session.exec(delete(User))
    session.commit()


def create_user(user: User, session: Session):
    """create a user in the db"""
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
