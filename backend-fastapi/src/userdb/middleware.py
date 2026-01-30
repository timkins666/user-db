from typing import Callable

from fastapi import Request
from fastapi.responses import JSONResponse

from userdb import auth
from userdb.utils import log


_logger = log.get_logger(__name__)

EXEMPT_PATH_PREFIXES = (
    "/auth",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon.ico",
    "/",
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
            _logger.critical("JWT auth middleware skipping auth path: %s", path)

            return await call_next(request)

    _logger.critical("JWT auth middleware checking path: %s", path)

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

    try:
        payload = auth.verify_access_token(token)
    except Exception as exc:
        # auth.verify_access_token raises HTTPException on error; mirror that
        detail = getattr(exc, "detail", "Invalid token")
        status_code = getattr(exc, "status_code", 401)
        return JSONResponse(status_code=status_code, content={"detail": detail})

    # attach user info for downstream use
    request.state.user = payload.get("sub")

    return await call_next(request)
