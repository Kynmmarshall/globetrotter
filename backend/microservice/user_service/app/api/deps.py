"""Shared FastAPI dependencies: current-user extraction and CSRF checks."""

from __future__ import annotations

import jwt
from fastapi import Request

from app.core.config import settings
from app.core.errors import forbidden, unauthorized
from app.core.security import decode_access_token
from app.models import User
from app.repositories import users as users_repo
from app.store import store


def _extract_token(request: Request) -> str | None:
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header[7:]
    return request.cookies.get(settings.access_cookie_name)


def _resolve_user(request: Request) -> User | None:
    token = _extract_token(request)
    if not token:
        return None
    try:
        claims = decode_access_token(token)
    except jwt.PyJWTError:
        return None

    user = users_repo.get_user_by_id(store.read(), claims.get("sub", ""))
    if user is None:
        return None
    if claims.get("tv") != user["token_version"]:
        # Password change / logout-everywhere / ban happened after this token was issued.
        return None
    return user


def get_current_user(request: Request) -> User:
    user = _resolve_user(request)
    if user is None:
        raise unauthorized("Please log in to continue.")
    return user


def get_current_user_optional(request: Request) -> User | None:
    return _resolve_user(request)


def require_csrf(request: Request) -> None:
    """Double-submit CSRF check for cookie-authenticated, state-changing requests.

    Requests authenticated via an `Authorization: Bearer` header (not a
    cookie) are exempt: CSRF only applies to ambient credentials a browser
    attaches automatically.
    """
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return

    cookie_value = request.cookies.get(settings.csrf_cookie_name)
    header_value = request.headers.get(settings.csrf_header_name)
    if not cookie_value or not header_value or cookie_value != header_value:
        raise forbidden("Missing or invalid CSRF token.")
