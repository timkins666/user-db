"""tests for auth router"""

# pylint: disable=missing-function-docstring

from __future__ import annotations

from userdb import redis as redis_store


def test_login_sets_cookie_and_returns_access_token(app):
    resp = app.post("/auth/login", json={"username": "alice", "password": "pw"})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data.get("access_token"), str)

    set_cookie = resp.headers.get("set-cookie", "")
    assert "refresh_token=" in set_cookie
    assert "Path=/auth/refresh" in set_cookie


def test_refresh_rotates_token_and_returns_access_token(app):
    login_resp = app.post("/auth/login", json={"username": "bob", "password": "pw"})
    assert login_resp.status_code == 200

    refresh_resp = app.post("/auth/refresh")
    assert refresh_resp.status_code == 200
    data = refresh_resp.json()
    assert isinstance(data.get("access_token"), str)

    # refresh should rotate cookie
    set_cookie = refresh_resp.headers.get("set-cookie", "")
    assert "refresh_token=" in set_cookie


def test_refresh_missing_cookie_401(app):
    # Ensure no cookie is present
    app.cookies.clear()
    resp = app.post("/auth/refresh")
    assert resp.status_code == 401


def test_refresh_reuse_old_cookie_fails(app):
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


def test_logout_revokes_refresh_and_access_token(app):
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


def test_logout_clears_refresh_cookie(app):
    login_resp = app.post("/auth/login", json={"username": "dave", "password": "pw"})
    assert login_resp.status_code == 200

    logout_resp = app.post("/auth/logout")
    assert logout_resp.status_code == 204

    set_cookie = logout_resp.headers.get("set-cookie", "")
    assert "refresh_token=" in set_cookie
    assert "Path=/auth/refresh" in set_cookie
    # Starlette sets Max-Age=0 when deleting cookies.
    assert "Max-Age=0" in set_cookie


def test_logout_bulk_revokes_all_refresh_tokens_for_user(app):
    # Create multiple refresh tokens for the same user (e.g., multiple sessions).
    login1 = app.post("/auth/login", json={"username": "erin", "password": "pw"})
    assert login1.status_code == 200
    refresh1 = login1.cookies.get("refresh_token")
    assert refresh1

    # Second login creates another refresh token for same normalized user.
    app.cookies.clear()
    login2 = app.post("/auth/login", json={"username": "Erin", "password": "pw"})
    assert login2.status_code == 200
    refresh2 = login2.cookies.get("refresh_token")
    assert refresh2
    assert refresh2 != refresh1

    # Note: refresh cookie Path is /auth/refresh, so it won't be sent to /auth/logout.
    # Provide an access token so logout can derive the username for bulk revocation.
    access_token = login2.json().get("access_token")
    assert isinstance(access_token, str)
    app.headers["Authorization"] = f"Bearer {access_token}"

    # Logout should revoke the current cookie token and bulk revoke the indexed ones.
    logout_resp = app.post("/auth/logout")
    assert logout_resp.status_code == 204

    # Replaying either refresh token should fail.
    app.cookies.clear()
    app.cookies.set("refresh_token", refresh1)
    resp1 = app.post("/auth/refresh")
    assert resp1.status_code == 401

    app.cookies.clear()
    app.cookies.set("refresh_token", refresh2)
    resp2 = app.post("/auth/refresh")
    assert resp2.status_code == 401


def test_logout_revokes_access_token_in_redis(app, fake_redis):
    login_resp = app.post("/auth/login", json={"username": "frank", "password": "pw"})
    assert login_resp.status_code == 200

    access_token = login_resp.json().get("access_token")
    assert isinstance(access_token, str)

    # Call logout presenting only the access token.
    app.cookies.clear()
    app.headers["Authorization"] = f"Bearer {access_token}"
    logout_resp = app.post("/auth/logout")
    assert logout_resp.status_code == 204

    # Verify a revocation key was set in Redis.
    revoked_key = redis_store.revoked_access_token_key(access_token)
    assert fake_redis.get(revoked_key) == "1"
