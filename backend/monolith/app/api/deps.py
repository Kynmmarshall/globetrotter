from __future__ import annotations

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.errors import unauthorized
from app.core.security import decode_access_token
from app.services.auth_service import get_user_or_raise

_bearer = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    if credentials is None:
        raise unauthorized("Missing bearer token.")
    try:
        user_id = decode_access_token(credentials.credentials)
    except jwt.PyJWTError as exc:
        raise unauthorized("Invalid or expired token.") from exc
    await get_user_or_raise(user_id)
    return user_id
