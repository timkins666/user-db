"""Redis helpers for auth token storage and revocation.

We use Redis for:
- refresh token state (existence == valid) and per-user token tracking
- access token revocation (hashed token key with TTL)
"""

from __future__ import annotations

import hashlib
import os

from redis import Redis


_redis_client: Redis | None = None


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


def refresh_token_key(refresh_token: str) -> str:
    return f"refresh_token:{refresh_token}"


def user_refresh_tokens_key(username: str) -> str:
    # Username should already be normalized (lowercase) by the caller.
    return f"user_refresh_tokens:{username}"


def revoked_access_token_key(access_token: str) -> str:
    token_hash = hashlib.sha256(access_token.encode("utf-8")).hexdigest()
    return f"revoked_access:{token_hash}"


def revoke_access_token(access_token: str, *, ttl_seconds: int) -> None:
    if ttl_seconds <= 0:
        return
    get_redis().set(revoked_access_token_key(access_token), "1", ex=ttl_seconds)


def is_access_token_revoked(access_token: str) -> bool:
    return get_redis().get(revoked_access_token_key(access_token)) is not None
