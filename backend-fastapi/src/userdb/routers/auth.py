"""auth http handlers"""

import json
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Body, Cookie, HTTPException, Response
from redis import Redis
from userdb import auth
from userdb.utils import log

_logger = log.get_logger(__name__)


router = APIRouter(prefix="/auth")

_redis_client: Redis | None = None


def _redis_key(refresh_token: str) -> str:
    return f"refresh_token:{refresh_token}"


def get_redis() -> Redis:
    global _redis_client
    if _redis_client is None:
        host = os.environ.get("REDIS_HOST", "redis")
        port = int(os.environ.get("REDIS_PORT", "6379"))
        db = int(os.environ.get("REDIS_DB", "0"))
        _redis_client = Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True,
        )
    return _redis_client


_GETDEL_LUA = """
local v = redis.call('GET', KEYS[1])
if v then
  redis.call('DEL', KEYS[1])
end
return v
""".strip()


def _redis_getdel(client: Redis, key: str) -> str | None:
    # Use Lua for atomic get+delete across Redis versions.
    return client.eval(_GETDEL_LUA, 1, key)


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


@router.post("/login")
def login(
    username: str = Body(...),
    password: str = Body(...),
):
    """
    simple login that always returns tokens,
    don't care about passwords right now
    """

    if True:
        _logger.info("username: %s, password: %s", username, password)

    refresh_token = auth.create_refresh_token(user_id=username)

    token_info = {
        "user": username,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    get_redis().set(
        _redis_key(refresh_token),
        json.dumps(token_info),
        ex=auth.REFRESH_TOKEN_EXPIRE_SECONDS,
    )

    from fastapi.responses import JSONResponse

    access_token = auth.create_access_token(subject=username)

    resp = JSONResponse({"access_token": access_token, "token_type": "bearer"})
    _set_refresh_cookie(resp, refresh_token)
    return resp


@router.post("/refresh")
def refresh(refresh_token: str | None = Cookie(default=None), *, response: Response):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing cookie")

    client = get_redis()
    token_info_raw = _redis_getdel(client, _redis_key(refresh_token))
    if not token_info_raw:
        raise HTTPException(status_code=401, detail="Token doesn't exist")

    try:
        token_info = json.loads(token_info_raw)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    if token_info.get("revoked"):
        raise HTTPException(status_code=401, detail="Token revoked")

    username = token_info.get("user")
    if not username:
        raise HTTPException(status_code=401, detail="Missing user in token info")
    new_token = auth.create_refresh_token(user_id=username)
    _set_refresh_cookie(response, new_token)

    new_token_info = {
        "user": username,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    client.set(
        _redis_key(new_token),
        json.dumps(new_token_info),
        ex=auth.REFRESH_TOKEN_EXPIRE_SECONDS,
    )

    access_token = auth.create_access_token(subject=username)
    return {"access_token": access_token, "token_type": "bearer"}
