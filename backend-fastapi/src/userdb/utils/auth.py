"""auth and refresh token stuff"""

from datetime import datetime, timedelta, timezone
from enum import StrEnum
import os
from typing import Any
import uuid

from fastapi import Depends, HTTPException, Request
import jwt

REFRESH_TOKEN_EXPIRE_SECONDS = 60 * 3
ACCESS_TOKEN_EXPIRE_MINUTES = 1.5
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-secret")
JWT_ALGORITHM = "HS256"
CLAIM_TYPE_ACCESS = "access"


class CurrentUser:
    """Authenticated user attached to the request."""

    def __init__(self, username: str, roles: list[str]):
        self.username = username
        self.roles = roles


class Role(StrEnum):
    """Supported roles for authorization checks."""

    USER = "user"
    ADMIN = "admin"


def create_refresh_token(user_id: str) -> str:
    """Create a dummy refresh token for the user."""

    return f"refresh-{user_id}-{uuid.uuid4()}"


def create_access_token(
    *,
    subject: str,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a signed short-lived access JWT."""

    now = datetime.now(timezone.utc)

    payload: dict[str, Any] = {
        "sub": subject.lower(),
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": CLAIM_TYPE_ACCESS,
    }

    if extra_claims:
        payload.update(extra_claims)

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def verify_access_token(token: str) -> dict:
    """Verify an access JWT and return its payload, or raise HTTPException."""

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )

        if payload.get("type") != CLAIM_TYPE_ACCESS:
            raise HTTPException(status_code=401, detail="Invalid token")

        if not payload.get("sub"):
            raise HTTPException(status_code=401, detail="Invalid token")

        return payload

    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc


async def get_current_user(request: Request) -> CurrentUser:
    """Dependency to get the current authenticated user from the request."""

    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def require_roles(*required_roles: str):
    """Dependency factory to require specific roles for a route."""

    async def role_checker(user=Depends(get_current_user)):
        if not set(user.roles or []).intersection(required_roles):
            raise HTTPException(403, "Forbidden")
        return user

    return role_checker
