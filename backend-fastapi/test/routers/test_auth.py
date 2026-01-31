"""tests for auth router"""

from __future__ import annotations

import time

import pytest


class FakeRedis:
    def __init__(self):
        self._store: dict[str, tuple[str, float | None]] = {}

    def set(self, key: str, value: str, ex: int | None = None):
        expires_at = (time.time() + ex) if ex is not None else None
        self._store[key] = (value, expires_at)
        return True

    def get(self, key: str):
        item = self._store.get(key)
        if not item:
            return None
        value, expires_at = item
        if expires_at is not None and time.time() >= expires_at:
            self._store.pop(key, None)
            return None
        return value

    def delete(self, key: str):
        return 1 if self._store.pop(key, None) is not None else 0

    def eval(self, _script: str, _numkeys: int, key: str):
        # Implements the get+del Lua behavior used by the app.
        val = self.get(key)
        if val is not None:
            self.delete(key)
        return val


@pytest.fixture()
def fake_redis(monkeypatch):
    from userdb.routers import auth as auth_router

    r = FakeRedis()
    monkeypatch.setattr(auth_router, "get_redis", lambda: r)
    yield r


def test_login_sets_cookie_and_returns_access_token(app, fake_redis):
    resp = app.post("/auth/login", json={"username": "alice", "password": "pw"})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data.get("access_token"), str)

    set_cookie = resp.headers.get("set-cookie", "")
    assert "refresh_token=" in set_cookie
    assert "Path=/auth/refresh" in set_cookie


def test_refresh_rotates_token_and_returns_access_token(app, fake_redis):
    login_resp = app.post("/auth/login", json={"username": "bob", "password": "pw"})
    assert login_resp.status_code == 200

    refresh_resp = app.post("/auth/refresh")
    assert refresh_resp.status_code == 200
    data = refresh_resp.json()
    assert isinstance(data.get("access_token"), str)

    # refresh should rotate cookie
    set_cookie = refresh_resp.headers.get("set-cookie", "")
    assert "refresh_token=" in set_cookie


def test_refresh_missing_cookie_401(app, fake_redis):
    # Ensure no cookie is present
    app.cookies.clear()
    resp = app.post("/auth/refresh")
    assert resp.status_code == 401


def test_refresh_reuse_old_cookie_fails(app, fake_redis):
    login_resp = app.post("/auth/login", json={"username": "carol", "password": "pw"})
    assert login_resp.status_code == 200

    first_refresh = app.post("/auth/refresh")
    assert first_refresh.status_code == 200

    # Second refresh uses the new cookie; capture the old cookie value manually
    # by replaying the first refresh cookie value should work, but reusing the *consumed*
    # login cookie should fail.
    app.cookies.clear()

    # Extract consumed token from login response and attempt refresh with it.
    consumed_cookie = login_resp.cookies.get("refresh_token")
    assert consumed_cookie

    app.cookies.set("refresh_token", consumed_cookie)

    resp = app.post("/auth/refresh")
    assert resp.status_code == 401
