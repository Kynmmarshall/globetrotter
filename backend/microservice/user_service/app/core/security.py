"""Password hashing and RS256 JWT helpers for the User Service.

The User Service is the ONLY service that holds the private key and can mint
access tokens. Itinerary/Recommendation services verify tokens using only the
public key (see app/core/config.py and PROJECT_PLAN.md section 13).
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import settings

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def _read_key(path: Any) -> str:
    return path.read_text(encoding="utf-8")


def create_access_token(user_id: str, token_version: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_access_token_minutes),
        "iss": settings.jwt_issuer,
        "tv": token_version,
        "jti": str(uuid.uuid4()),
    }
    private_key = _read_key(settings.jwt_private_key_path)
    return jwt.encode(payload, private_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Return the decoded claims of a valid access token.

    Raises jwt.PyJWTError (or a subclass) for any invalid/expired token.
    """
    public_key = _read_key(settings.jwt_public_key_path)
    return jwt.decode(
        token,
        public_key,
        algorithms=[settings.jwt_algorithm],
        issuer=settings.jwt_issuer,
    )


def new_refresh_token() -> str:
    """An opaque, high-entropy refresh token. Only its hash is stored server-side."""
    return uuid.uuid4().hex + uuid.uuid4().hex


def hash_refresh_token(token: str) -> str:
    # Refresh tokens are already high-entropy random strings (not user-chosen
    # passwords), so a fast, deterministic hash is sufficient and lets lookups
    # use an indexed equality query instead of scanning and verifying each row.
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
