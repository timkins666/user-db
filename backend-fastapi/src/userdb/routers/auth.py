"""auth http handlers"""

import json
import time
from datetime import datetime, timezone
from json import JSONDecodeError

from fastapi import APIRouter, Body, Cookie, HTTPException, Request, Response
from fastapi.responses import JSONResponse

import jwt

from userdb.utils import auth
from userdb import redis as redis_store
from userdb.utils import log

_logger = log.get_logger(__name__)


router = APIRouter(prefix="/auth")


# Redis atomic get+delete and refresh helpers moved into userdb.redis


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
    """Decode a JWT without verifying exp; returns payload or None."""
    try:
        return jwt.decode(
            access_token,
            auth.JWT_SECRET_KEY,
            algorithms=[auth.JWT_ALGORITHM],
            options={"verify_exp": False},
        )
    except jwt.PyJWTError:
        return None


@router.post("/login")
async def login(
    username: str = Body(...),
    password: str = Body(...),
):
    """Login endpoint.

    Currently accepts any username/password and returns access+refresh tokens.
    """

    _logger.info("username: %s, password: %s", username, password)

    username_lower = username.lower()
    refresh_token = auth.create_refresh_token(user_id=username_lower)

    token_info = {
        "user": username_lower,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    # Store refresh token and index it for the user
    await redis_store.set_refresh_token(
        refresh_token,
        json.dumps(token_info),
        ex_seconds=auth.REFRESH_TOKEN_EXPIRE_SECONDS,
    )
    await redis_store.add_user_refresh_token(
        username_lower, refresh_token, ex_seconds=auth.REFRESH_TOKEN_EXPIRE_SECONDS
    )

    access_token = auth.create_access_token(subject=username_lower)

    resp = _access_token_response(access_token)
    _set_refresh_cookie(resp, refresh_token)
    return resp


@router.post("/refresh")
async def refresh(refresh_token: str | None = Cookie(default=None)):
    """Rotate refresh token and return a new access token."""
    if not refresh_token:
        raise HTTPException(status_code=401)

    token_info_raw = await redis_store.get_refresh_token(refresh_token)
    if not token_info_raw:
        raise HTTPException(status_code=401)

    try:
        token_info = json.loads(token_info_raw)
    except (JSONDecodeError, TypeError) as exc:
        raise HTTPException(status_code=401) from exc

    if token_info.get("revoked"):
        raise HTTPException(status_code=401)

    username = token_info.get("user")
    if not username:
        raise HTTPException(status_code=401)
    new_token = auth.create_refresh_token(user_id=username)

    # Maintain per-user refresh token index
    # Maintain per-user refresh token index (remove old, add new)
    await redis_store.remove_user_refresh_token(username, refresh_token)
    await redis_store.add_user_refresh_token(
        username, new_token, ex_seconds=auth.REFRESH_TOKEN_EXPIRE_SECONDS
    )

    new_token_info = {
        "user": username,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await redis_store.set_refresh_token(
        new_token,
        json.dumps(new_token_info),
        ex_seconds=auth.REFRESH_TOKEN_EXPIRE_SECONDS,
    )

    # Delete the old refresh token after rotation completes successfully.
    await redis_store.delete_refresh_token(refresh_token)

    access_token = auth.create_access_token(subject=username)
    response = _access_token_response(access_token)
    _set_refresh_cookie(response, new_token)
    return response


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

    # Use redis helpers for token operations
    # Redis helpers handle operations below

    username: str | None = None

    # Best-effort: if we still have refresh token info, extract username for bulk revoke.
    if refresh_token:
        raw = redis_store.get_refresh_token(refresh_token)
        if isinstance(raw, str) and raw:
            try:
                username = (json.loads(raw) or {}).get("user")
            except (JSONDecodeError, TypeError):
                username = None

        # Revoke the cookie refresh token.
        await redis_store.delete_refresh_token(refresh_token)

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
                await redis_store.revoke_access_token(access_token, ttl_seconds=ttl)
            else:
                # Fallback: if exp missing/unexpected, revoke for a short window.
                await redis_store.revoke_access_token(access_token, ttl_seconds=60)

    # Bulk revoke any other refresh tokens for the user.
    if username:
        tokens = await redis_store.get_user_refresh_tokens(username)
        for t in tokens:
            if isinstance(t, str) and t:
                await redis_store.delete_refresh_token(t)
        await redis_store.delete_user_refresh_tokens(username)
    resp = Response(status_code=204)
    _clear_refresh_cookie(resp)
    return resp
