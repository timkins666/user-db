"""auth http handlers"""

from datetime import datetime, timezone

from fastapi import APIRouter, Body, Cookie, HTTPException, Response
from userdb import auth
from userdb.utils import log

_logger = log.get_logger(__name__)

router = APIRouter(prefix="/auth")

mock_refresh_tokens: dict[str, dict] = {}


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

    # pretend it's in a db
    mock_refresh_tokens[refresh_token] = {
        "user": username,
        "created_at": datetime.now(timezone.utc),
    }

    from fastapi.responses import JSONResponse

    access_token = auth.create_access_token(subject=username)

    resp = JSONResponse({"access_token": access_token, "token_type": "bearer"})
    _set_refresh_cookie(resp, refresh_token)
    return resp


@router.post("/refresh")
def refresh(refresh_token: str | None = Cookie(default=None), *, response: Response):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing cookie")

    token_info = mock_refresh_tokens.pop(refresh_token, None)
    if not token_info:
        raise HTTPException(status_code=401, detail="Token doesn't exist")

    if token_info.get("revoked"):
        raise HTTPException(status_code=401, detail="Token revoked")

    username = token_info.get("user")
    if not username:
        raise HTTPException(status_code=401, detail="Missing user in token info")
    new_token = auth.create_refresh_token(user_id=username)
    _set_refresh_cookie(response, new_token)

    # set in fake db
    mock_refresh_tokens[new_token] = {
        "user": username,
        "created_at": datetime.now(timezone.utc),
    }

    access_token = auth.create_access_token(subject=username)
    return {"access_token": access_token, "token_type": "bearer"}
