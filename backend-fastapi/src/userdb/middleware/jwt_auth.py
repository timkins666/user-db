"""JWT auth middleware.

Validates Bearer JWTs on protected endpoints and checks Redis-backed
access-token revocation.
"""

from typing import Callable

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from userdb.utils import auth, log
from userdb.redis import is_access_token_revoked


_logger = log.get_logger(__name__)

EXEMPT_PATH_PREFIXES = (
    "/auth",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon.ico",
    "/",
)


def get_user_from_token(payload: dict) -> auth.CurrentUser:
    """
    tmp.
    extract username identifier from JWT payload.
    adds roles, all admins for now.
    """
    return auth.CurrentUser(
        username=payload["sub"],
        roles=[auth.Role.USER, auth.Role.ADMIN],
    )


async def jwt_auth_middleware(request: Request, call_next: Callable):
    """HTTP middleware that validates a Bearer JWT in the Authorization header.

    - Skips validation for common public paths (auth endpoints, docs, root).
    - On success attaches `request.state.user` (the `sub` claim) for downstream handlers.
    - Returns 401 JSON responses for missing/invalid/expired tokens.
    """
    path = request.url.path

    # Allow public paths
    for prefix in EXEMPT_PATH_PREFIXES:
        if path == prefix or path.startswith(prefix + "/"):
            _logger.debug("JWT auth middleware skipping auth path: %s", path)

            return await call_next(request)

    _logger.debug("JWT auth middleware checking path: %s", path)

    # Allow preflight
    if request.method == "OPTIONS":
        return await call_next(request)

    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        return JSONResponse(
            status_code=401,
            content={"detail": "Missing or invalid Authorization header"},
        )

    token = auth_header.split(" ", 1)[1].strip()

    if is_access_token_revoked(token):
        return JSONResponse(
            status_code=401,
            content={"detail": "Token revoked"},
        )

    try:
        payload = auth.verify_access_token(token)
    except HTTPException as exc:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    request.state.user = get_user_from_token(payload)

    return await call_next(request)
