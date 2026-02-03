"""common test setup"""

# pylint: disable=missing-function-docstring,missing-class-docstring

import time

from fastapi.testclient import TestClient
import pytest
from sqlmodel import Session, SQLModel, create_engine, delete
from sqlmodel.pool import StaticPool

from userdb.utils import auth
from userdb.db import get_session
from userdb.main import app as fastapi_app
from userdb.models.user import User
from userdb import redis as redis_store


@pytest.fixture(name="app", scope="session")
def _app(session):
    """
    FastAPI TestClient app fixture.
    Overrides `get_session` to use sqlite db.
    """

    def get_session_override():
        return session

    fastapi_app.dependency_overrides[get_session] = get_session_override
    yield TestClient(fastapi_app)


@pytest.fixture(autouse=True)
def _clear_client_state(app: TestClient) -> None:
    """clear cookies and auth headers from TestClient to keep tests isolated"""
    app.cookies.clear()
    app.headers.pop("Authorization", None)


@pytest.fixture
def set_current_user():
    """fixture to provide result of get_current_user"""

    def _set(user: auth.CurrentUser):
        fastapi_app.dependency_overrides[auth.get_current_user] = lambda: user

    yield _set


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


@pytest.fixture(name="username")
def _username():
    return "test-user"


@pytest.fixture()
def access_token(username):
    return auth.create_access_token(subject=username)


class FakeRedis:
    """Minimal in-memory Redis double for tests."""

    def __init__(self):
        self._store: dict[str, tuple[str | set[str], float | None]] = {}

    def _is_expired(self, key: str) -> bool:
        item = self._store.get(key)
        if not item:
            return True
        _value, expires_at = item
        if expires_at is not None and time.time() >= expires_at:
            self._store.pop(key, None)
            return True
        return False

    def set(self, key: str, value: str, ex: int | None = None):
        expires_at = (time.time() + ex) if ex is not None else None
        self._store[key] = (value, expires_at)
        return True

    def get(self, key: str):
        if self._is_expired(key):
            return None
        value, _expires_at = self._store[key]
        return value

    def delete(self, key: str):
        return 1 if self._store.pop(key, None) is not None else 0

    def expire(self, key: str, ex: int):
        if self._is_expired(key):
            return False
        value, _ = self._store[key]
        self._store[key] = (value, time.time() + ex)
        return True

    def sadd(self, key: str, member: str):
        if self._is_expired(key):
            current: set[str] = set()
            expires_at = None
        else:
            value, expires_at = self._store[key]
            current = set(value) if isinstance(value, set) else set()

        added = 0 if member in current else 1
        current.add(member)
        self._store[key] = (current, expires_at)
        return added

    def srem(self, key: str, member: str):
        if self._is_expired(key):
            return 0
        value, expires_at = self._store[key]
        if not isinstance(value, set):
            return 0
        removed = 1 if member in value else 0
        value.discard(member)
        self._store[key] = (value, expires_at)
        return removed

    def smembers(self, key: str):
        if self._is_expired(key):
            return set()
        value, _expires_at = self._store[key]
        if isinstance(value, set):
            return set(value)
        return set()

    def eval(self, _script: str, _numkeys: int, key: str):
        # Implements the get+del Lua behavior used by the app.
        val = self.get(key)
        if val is not None:
            self.delete(key)
        return val


@pytest.fixture(autouse=True)
def fake_redis(monkeypatch):
    r = FakeRedis()
    monkeypatch.setattr(redis_store, redis_store.get_redis.__name__, lambda: r)
    yield r
