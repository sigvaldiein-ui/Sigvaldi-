"""Auth middleware — Sprint 73 Fasi 3: JWT session úr httpOnly cookie."""
import logging
import os
import uuid
from datetime import datetime, timezone, timedelta

import jwt
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("alvitur.auth")

JWT_SECRET = os.getenv("JWT_SECRET") or os.getenv("MASTER_KEY")
if not JWT_SECRET or len(JWT_SECRET) < 32:
    raise RuntimeError("JWT_SECRET (or MASTER_KEY) must be set, min 32 chars")

JWT_ALGORITHM = "HS256"
COOKIE_NAME = "alvitur_session"
ACCESS_TOKEN_TTL = timedelta(minutes=15)


def create_session_token(user_id: int, kennitala_hash: str) -> str:
    """Býr til JWT session token."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "kennitala_hash": kennitala_hash,
        "iat": now,
        "exp": now + ACCESS_TOKEN_TTL,
        "iss": "alvitur.is",
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_session_token(token: str) -> dict:
    """Les JWT session token. Kastar ef ógilt."""
    return jwt.decode(
        token,
        JWT_SECRET,
        algorithms=["HS256"],
        issuer="alvitur.is",
        options={"require": ["exp", "iat", "sub", "jti"]},
        leeway=30,
    )


class AuthMiddleware(BaseHTTPMiddleware):
    """Setur user_info í request.state ef JWT cookie er til staðar."""

    async def dispatch(self, request: Request, call_next):
        token = request.cookies.get(COOKIE_NAME)
        if token:
            try:
                payload = decode_session_token(token)
                request.state.user = {
                    "user_id": int(payload["sub"]),
                    "kennitala_hash": payload["kennitala_hash"],
                }
            except jwt.InvalidTokenError:
                request.state.user = None
        else:
            request.state.user = None

        response = await call_next(request)
        return response
