"""auth and refresh token stuff"""

import os
from datetime import datetime, timedelta, timezone
from typing import Any
import uuid

from fastapi import HTTPException
import jwt

REFRESH_TOKEN_EXPIRE_SECONDS = 60 * 3
ACCESS_TOKEN_EXPIRE_MINUTES = 1.5
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-secret")
JWT_ALGORITHM = "HS256"
CLAIM_TYPE_ACCESS = "access"


def create_refresh_token(user_id: str) -> str:
    """Create a dummy refresh token for the user."""
    return f"refresh-{user_id}-{uuid.uuid4()}"


def create_access_token(
    *,
    subject: str,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(timezone.utc)

    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": CLAIM_TYPE_ACCESS,
    }

    if extra_claims:
        payload.update(extra_claims)

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def verify_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )

        if payload.get("type") != CLAIM_TYPE_ACCESS:
            raise HTTPException(status_code=401, detail="Invalid token type")

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
