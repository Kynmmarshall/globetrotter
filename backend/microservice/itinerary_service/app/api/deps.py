"""JWT verification using ONLY the User Service's public key (no DB user lookup).

Same trade-off as the Recommendation Service: no synchronous call back to the
User Service on every request; revocation takes effect at token expiry.
"""

from __future__ import annotations

import jwt
from fastapi import Request

from app.core.config import settings
from app.core.errors import unauthorized

_public_key_cache: str | None = None


def _public_key() -> str:
    global _public_key_cache
    if _public_key_cache is None:
        _public_key_cache = settings.jwt_public_key_path.read_text(encoding="utf-8")
    return _public_key_cache


def _extract_token(request: Request) -> str | None:
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header[7:]
    return request.cookies.get("gt_access")


def get_current_user_id(request: Request) -> str:
    token = _extract_token(request)
    if not token:
        raise unauthorized()
    try:
        claims = jwt.decode(token, _public_key(), algorithms=[settings.jwt_algorithm], issuer=settings.jwt_issuer)
    except jwt.PyJWTError:
        raise unauthorized() from None
    return claims["sub"]
