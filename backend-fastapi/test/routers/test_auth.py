"""tests for auth router"""

from __future__ import annotations

import time

import pytest


class FakeRedis:
    def __init__(self):
        self._store: dict[str, tuple[str, float | None]] = {}

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


@pytest.fixture()
def fake_redis(monkeypatch):
    from userdb import redis as redis_store

    r = FakeRedis()
    monkeypatch.setattr(redis_store, "get_redis", lambda: r)
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


def test_logout_revokes_refresh_and_access_token(app, fake_redis):
    login_resp = app.post("/auth/login", json={"username": "Alice", "password": "pw"})
    assert login_resp.status_code == 200
    access_token = login_resp.json().get("access_token")
    assert isinstance(access_token, str)

    # Capture refresh token for replay attempt after logout.
    refresh_token = login_resp.cookies.get("refresh_token")
    assert refresh_token

    # Access token should work before logout.
    app.headers["Authorization"] = f"Bearer {access_token}"
    users_before = app.get("/users")
    assert users_before.status_code == 200

    logout_resp = app.post("/auth/logout")
    assert logout_resp.status_code == 204

    # Replaying the old refresh token should fail.
    app.cookies.clear()
    app.cookies.set("refresh_token", refresh_token)
    refresh_after = app.post("/auth/refresh")
    assert refresh_after.status_code == 401

    # The old access token should now be rejected by middleware.
    users_after = app.get("/users")
    assert users_after.status_code == 401
