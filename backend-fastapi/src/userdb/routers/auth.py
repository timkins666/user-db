"""auth http handlers"""

import json
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Body, Cookie, HTTPException, Request, Response
from fastapi.responses import JSONResponse

import jwt

from userdb import auth
from userdb import redis as redis_store
from userdb.utils import log

_logger = log.get_logger(__name__)


router = APIRouter(prefix="/auth")


_GETDEL_LUA = """
local v = redis.call('GET', KEYS[1])
if v then
  redis.call('DEL', KEYS[1])
end
return v
""".strip()


def _redis_getdel(client, key: str) -> str | None:
    # Use Lua for atomic get+delete across Redis versions.
    return client.eval(_GETDEL_LUA, 1, key)


def _access_token_response(access_token: str) -> JSONResponse:
    return JSONResponse({"access_token": access_token, "token_type": "bearer"})


def _set_refresh_cookie(
    response: Response,
    refresh_token: str,
):
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        # dev settings
        secure=False,
        samesite="lax",
        path="/auth/refresh",
        max_age=auth.REFRESH_TOKEN_EXPIRE_SECONDS,
    )


def _clear_refresh_cookie(response: Response) -> None:
    # Must match the path used when setting the cookie.
    response.delete_cookie(
        key="refresh_token",
        path="/auth/refresh",
        secure=False,
        samesite="lax",
    )


def _decode_access_token_allow_expired(access_token: str) -> dict | None:
    try:
        return jwt.decode(
            access_token,
            auth.JWT_SECRET_KEY,
            algorithms=[auth.JWT_ALGORITHM],
            options={"verify_exp": False},
        )
    except Exception:
        return None


@router.post("/login")
async def login(
    username: str = Body(...),
    password: str = Body(...),
):
    """
    simple login that always returns tokens,
    don't care about passwords right now
    """

    if True:
        _logger.info("username: %s, password: %s", username, password)

    username_lower = username.lower()
    refresh_token = auth.create_refresh_token(user_id=username_lower)

    token_info = {
        "user": username_lower,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    client = redis_store.get_redis()
    client.set(
        redis_store.refresh_token_key(refresh_token),
        json.dumps(token_info),
        ex=auth.REFRESH_TOKEN_EXPIRE_SECONDS,
    )

    # Track all refresh tokens for this user so logout can revoke them.
    user_key = redis_store.user_refresh_tokens_key(username_lower)
    client.sadd(user_key, refresh_token)
    client.expire(user_key, auth.REFRESH_TOKEN_EXPIRE_SECONDS)

    access_token = auth.create_access_token(subject=username_lower)

    resp = _access_token_response(access_token)
    _set_refresh_cookie(resp, refresh_token)
    return resp


@router.post("/refresh")
async def refresh(
    refresh_token: str | None = Cookie(default=None), *, response: Response
):
    if not refresh_token:
        raise HTTPException(status_code=401)

    client = redis_store.get_redis()
    token_info_raw = _redis_getdel(client, redis_store.refresh_token_key(refresh_token))
    if not token_info_raw:
        raise HTTPException(status_code=401)

    try:
        token_info = json.loads(token_info_raw)
    except Exception:
        raise HTTPException(status_code=401)

    if token_info.get("revoked"):
        raise HTTPException(status_code=401)

    username = token_info.get("user")
    if not username:
        raise HTTPException(status_code=401)
    new_token = auth.create_refresh_token(user_id=username)
    _set_refresh_cookie(response, new_token)

    # Maintain per-user refresh token index
    user_key = redis_store.user_refresh_tokens_key(username)
    client.srem(user_key, refresh_token)
    client.sadd(user_key, new_token)
    client.expire(user_key, auth.REFRESH_TOKEN_EXPIRE_SECONDS)

    new_token_info = {
        "user": username,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    client.set(
        redis_store.refresh_token_key(new_token),
        json.dumps(new_token_info),
        ex=auth.REFRESH_TOKEN_EXPIRE_SECONDS,
    )

    access_token = auth.create_access_token(subject=username)
    return _access_token_response(access_token)


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    refresh_token: str | None = Cookie(default=None),
):
    """Logout revokes refresh tokens and the presented access token.

    - If a refresh cookie exists: revoke that cookie token.
    - If an Authorization bearer access token exists: mark it revoked in Redis until exp.
    - If a username can be determined: revoke all refresh tokens indexed for that user.
    """

    client = redis_store.get_redis()

    username: str | None = None

    # Best-effort: if we still have refresh token info, extract username for bulk revoke.
    if refresh_token:
        rt_key = redis_store.refresh_token_key(refresh_token)
        raw = client.get(rt_key)
        if isinstance(raw, str) and raw:
            try:
                username = (json.loads(raw) or {}).get("user")
            except Exception:
                username = None

        # Revoke the cookie refresh token.
        client.delete(rt_key)

    # Revoke the presented access token.
    auth_header = request.headers.get("authorization") or ""
    access_token: str | None = None
    if auth_header.lower().startswith("bearer "):
        access_token = auth_header.split(" ", 1)[1].strip()

    if access_token:
        payload = _decode_access_token_allow_expired(access_token)
        if payload and payload.get("type") == auth.CLAIM_TYPE_ACCESS:
            # Determine username (for bulk refresh revoke) + TTL for revocation entry.
            sub = payload.get("sub")
            if isinstance(sub, str) and sub:
                username = username or sub

            exp = payload.get("exp")
            if isinstance(exp, (int, float)):
                ttl = int(exp - time.time())
                redis_store.revoke_access_token(access_token, ttl_seconds=ttl)
            else:
                # Fallback: if exp missing/unexpected, revoke for a short window.
                redis_store.revoke_access_token(access_token, ttl_seconds=60)

    # Bulk revoke any other refresh tokens for the user.
    if username:
        user_key = redis_store.user_refresh_tokens_key(username)
        tokens = client.smembers(user_key)
        if not isinstance(tokens, (set, list, tuple)):
            tokens = []

        for t in tokens:
            if isinstance(t, str) and t:
                client.delete(redis_store.refresh_token_key(t))
        client.delete(user_key)

    resp = Response(status_code=204)
    _clear_refresh_cookie(resp)
    return resp
