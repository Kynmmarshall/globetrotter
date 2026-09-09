"""JWT verification using ONLY the User Service's public key (no DB user lookup here).

This service never mints tokens and has no users table; it trusts a validly
signed, unexpired access token's "sub" claim as the user id. Revocation
(logout-everywhere, bans) takes effect only when that token naturally expires
(<= JWT_ACCESS_TOKEN_MINUTES) -- an accepted trade-off for avoiding a
synchronous call back to the User Service on every request (plan section 7).
"""

from __future__ import annotations

import jwt
from fastapi import Request

from app.core.config import settings

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


def get_current_user_id_optional(request: Request) -> str | None:
    token = _extract_token(request)
    if not token:
        return None
    try:
        claims = jwt.decode(token, _public_key(), algorithms=[settings.jwt_algorithm], issuer=settings.jwt_issuer)
    except jwt.PyJWTError:
        return None
    return claims.get("sub")
