"""tests for middleware/jwt_auth.py

These tests exercise the middleware through the FastAPI TestClient to ensure
request/response behavior matches expectations.
"""

# pylint: disable=missing-function-docstring

from __future__ import annotations
from datetime import datetime, timedelta, timezone

import jwt

from userdb import redis as redis_store
from userdb.utils import auth


def test_exempt_paths_do_not_require_auth(app):
    root_resp = app.get("/")
    assert root_resp.status_code == 200

    login_resp = app.post("/auth/login", json={"username": "alice", "password": "pw"})
    assert login_resp.status_code == 200


def test_missing_authorization_header_returns_401(app):
    resp = app.get("/users")
    assert resp.status_code == 401
    assert resp.json().get("detail") == "Missing or invalid Authorization header"


def test_invalid_token_returns_401(app):
    app.headers["Authorization"] = "Bearer not-a-jwt"
    resp = app.get("/users")
    assert resp.status_code == 401
    assert resp.json().get("detail") == "Invalid token"


def test_expired_token_returns_401(app):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "someone",
        "iat": now - timedelta(minutes=10),
        "exp": now - timedelta(minutes=5),
        "type": auth.CLAIM_TYPE_ACCESS,
    }
    expired_token = jwt.encode(
        payload, auth.JWT_SECRET_KEY, algorithm=auth.JWT_ALGORITHM
    )

    app.headers["Authorization"] = f"Bearer {expired_token}"
    resp = app.get("/users")
    assert resp.status_code == 401
    assert resp.json().get("detail") == "Token expired"


def test_revoked_access_token_returns_401(app, fake_redis):
    token = auth.create_access_token(subject="revoked-user")
    revoked_key = redis_store.revoked_access_token_key(token)
    fake_redis.set(revoked_key, "1", ex=60)

    app.headers["Authorization"] = f"Bearer {token}"
    resp = app.get("/users")
    assert resp.status_code == 401
    assert resp.json().get("detail") == "Token revoked"


def test_valid_access_token_allows_protected_endpoint(app):
    token = auth.create_access_token(subject="ok-user")
    app.headers["Authorization"] = f"Bearer {token}"

    # /users is protected; should pass middleware and return an empty list.
    resp = app.get("/users")
    assert resp.status_code == 200
    assert resp.text == "[]"


def test_valid_access_token_sets_user_for_role_protected_endpoint(app):
    token = auth.create_access_token(subject="admin-user")
    app.headers["Authorization"] = f"Bearer {token}"

    # This endpoint requires admin role via dependency, which relies on request.state.user.
    resp = app.post(
        "/users/create",
        json={
            "user": {
                "firstname": "Test",
                "lastname": "User",
                "dateOfBirth": "2001-02-03",
            }
        },
    )
    assert resp.status_code == 200
