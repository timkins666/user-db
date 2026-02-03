"""Redis helpers for auth token storage and revocation.

We use Redis for:
- refresh token state (existence == valid) and per-user token tracking
- access token revocation (hashed token key with TTL)
"""

from __future__ import annotations

from functools import lru_cache
import hashlib
import os
from typing import Any

from redis import Redis


def get_redis() -> Redis:
    """Return a singleton Redis client (cached)."""
    return _get_redis_client()


@lru_cache(maxsize=1)
def _get_redis_client() -> Redis:
    host = os.environ.get("REDIS_HOST", "redis")
    port = int(os.environ.get("REDIS_PORT", "6379"))
    db = int(os.environ.get("REDIS_DB", "0"))
    return Redis(
        host=host,
        port=port,
        db=db,
        decode_responses=True,
    )


def refresh_token_key(refresh_token: str) -> str:
    """Redis key for a single refresh token."""
    return f"refresh_token:{refresh_token}"


def user_refresh_tokens_key(username: str) -> str:
    """Redis key for the set of refresh tokens for a user."""
    # Username should already be normalized (lowercase) by the caller.
    return f"user_refresh_tokens:{username}"


def revoked_access_token_key(access_token: str) -> str:
    """Redis key for revoked access token marker (sha256 hashed)."""
    token_hash = hashlib.sha256(access_token.encode("utf-8")).hexdigest()
    return f"revoked_access:{token_hash}"


def revoke_access_token(access_token: str, *, ttl_seconds: int) -> None:
    """Mark an access token as revoked until it expires."""
    if ttl_seconds <= 0:
        return
    get_redis().set(revoked_access_token_key(access_token), "1", ex=ttl_seconds)


def is_access_token_revoked(access_token: str) -> bool:
    """Return True if token has been revoked."""
    return get_redis().get(revoked_access_token_key(access_token)) is not None


def set_refresh_token(
    refresh_token: str, token_info_json: str, *, ex_seconds: int
) -> None:
    """Store refresh token payload in Redis."""
    get_redis().set(refresh_token_key(refresh_token), token_info_json, ex=ex_seconds)


def delete_refresh_token(refresh_token: str) -> None:
    """Delete a refresh token record from Redis."""
    get_redis().delete(refresh_token_key(refresh_token))


def add_user_refresh_token(
    username: str, refresh_token: str, *, ex_seconds: int
) -> None:
    """Index a refresh token under a user for bulk revocation."""
    key = user_refresh_tokens_key(username)
    get_redis().sadd(key, refresh_token)
    get_redis().expire(key, ex_seconds)


def remove_user_refresh_token(username: str, refresh_token: str) -> None:
    """Remove a refresh token from the user's index set."""
    key = user_refresh_tokens_key(username)
    get_redis().srem(key, refresh_token)


def get_user_refresh_tokens(username: str) -> Any:
    """Return the user's refresh token set members (type depends on Redis client)."""
    key = user_refresh_tokens_key(username)
    return get_redis().smembers(key)


def delete_user_refresh_tokens(username: str) -> None:
    """Delete the user's refresh-token index key."""
    key = user_refresh_tokens_key(username)
    get_redis().delete(key)


def get_refresh_token(refresh_token: str) -> Any:
    """Return raw stored value for a refresh token key (or None).

    Return type is Any to avoid redis client Awaitable typing mismatch.
    """
    return get_redis().get(refresh_token_key(refresh_token))
