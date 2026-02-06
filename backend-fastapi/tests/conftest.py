"""common test setup"""

# pylint: disable=missing-function-docstring,missing-class-docstring

import asyncio
import dataclasses
import os
import time
from unittest import mock

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
    Overrides `get_session` to use sqlite db and sets the default CurrentUser.
    """

    fastapi_app.dependency_overrides[get_session] = lambda: session
    yield TestClient(fastapi_app)


@pytest.fixture(autouse=True)
def _clear_client_state(app: TestClient):
    """
    Clear cookies and auth headers after each test to keep tests isolated
    """

    yield

    app.cookies.clear()
    app.headers.pop("Authorization", None)


@pytest.fixture(autouse=True)
def _set_default_user(set_current_user, default_user: auth.CurrentUser) -> None:
    """
    Set a default admin user for tests (can be overridden with set_current_user)
    """

    set_current_user(default_user)


@pytest.fixture(autouse=True)
def _set_default_auth_header(app: TestClient, access_token) -> None:
    """
    Set a default auth header for tests (can be overridden in individual tests)
    """

    app.headers["Authorization"] = f"Bearer {access_token}"


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


@dataclasses.dataclass(frozen=True, init=False)
class MockEnv:
    # pylint: disable=invalid-name
    UPLOAD_BUCKET_NAME: str = "test-bucket"
    UPLOAD_PATH_PREFIX: str = "test-uploads"
    CLEAN_PATH_PREFIX: str = "test-clean"
    AWS_REGION: str = "eu-west-1"
    DOCUMENT_PROCESSING_SFN_ARN: str = "sf_arn"


@pytest.fixture(autouse=True)
def default_env_vars():
    with mock.patch.dict(
        os.environ,
        dataclasses.asdict(MockEnv()),
    ):
        yield


@pytest.fixture(autouse=True, scope="session")
def patch_asyncio_sleep():
    actual_sleep = asyncio.sleep
    with mock.patch(
        "asyncio.sleep",
        lambda t: print(f"Simulated sleep for {t} seconds") or actual_sleep(0),
    ):
        yield


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
    return "alan.jenkins"


@pytest.fixture(name="default_user")
def _default_user(username: str):
    """return a default test user for requests"""
    return auth.CurrentUser(username=username, roles=[auth.Role.USER, auth.Role.ADMIN])


@pytest.fixture(name="set_current_user")
def _set_current_user():
    """fixture to provide result of get_current_user"""

    def _set(user: auth.CurrentUser):
        fastapi_app.dependency_overrides[auth.get_current_user] = lambda: user

    yield _set


@pytest.fixture(name="access_token")
def _access_token(username):
    return auth.create_access_token(subject=username)


class FakeRedis:
    """Minimal in-memory Redis double for tests."""

    def __init__(self):
        self._store: dict[str, tuple[str | set[str], float | None]] = {}

    async def _is_expired(self, key: str) -> bool:
        item = self._store.get(key)
        if not item:
            return True
        _value, expires_at = item
        if expires_at is not None and time.time() >= expires_at:
            self._store.pop(key, None)
            return True
        return False

    async def set(self, key: str, value: str, ex: int | None = None):
        expires_at = (time.time() + ex) if ex is not None else None
        self._store[key] = (value, expires_at)
        return True

    async def get(self, key: str):
        if await self._is_expired(key):
            return None
        value, _expires_at = self._store[key]
        return value

    async def delete(self, key: str):
        return 1 if self._store.pop(key, None) is not None else 0

    async def expire(self, key: str, ex: int):
        if await self._is_expired(key):
            return False
        value, _ = self._store[key]
        self._store[key] = (value, time.time() + ex)
        return True

    async def sadd(self, key: str, member: str):
        if await self._is_expired(key):
            current: set[str] = set()
            expires_at = None
        else:
            value, expires_at = self._store[key]
            current = set(value) if isinstance(value, set) else set()

        added = 0 if member in current else 1
        current.add(member)
        self._store[key] = (current, expires_at)
        return added

    async def srem(self, key: str, member: str):
        if await self._is_expired(key):
            return 0
        value, expires_at = self._store[key]
        if not isinstance(value, set):
            return 0
        removed = 1 if member in value else 0
        value.discard(member)
        self._store[key] = (value, expires_at)
        return removed

    async def smembers(self, key: str):
        if await self._is_expired(key):
            return set()
        value, _expires_at = self._store[key]
        if isinstance(value, set):
            return set(value)
        return set()

    async def eval(self, _script: str, _numkeys: int, key: str):
        # Implements the get+del Lua behavior used by the app.
        val = await self.get(key)
        if val is not None:
            await self.delete(key)
        return val


@pytest.fixture(autouse=True)
def fake_redis(monkeypatch):
    r = FakeRedis()
    monkeypatch.setattr(redis_store, redis_store.get_redis.__name__, lambda: r)
    yield r


mock.patch("asyncio.sleep")
