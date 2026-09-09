"""Registration, login, and refresh-token session management."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.config import settings
from app.core.errors import conflict, unauthorized
from app.core.security import (
    create_access_token,
    hash_password,
    hash_refresh_token,
    new_refresh_token,
    verify_password,
)
from app.models import User
from app.repositories import users as users_repo
from app.store import store


@dataclass
class IssuedSession:
    user: User
    access_token: str
    refresh_token: str
    csrf_token: str


def _issue_session(db: dict[str, Any], user: User, *, user_agent: str | None) -> IssuedSession:
    refresh_token = new_refresh_token()
    users_repo.create_refresh_session(
        db,
        user_id=user["id"],
        token_hash=hash_refresh_token(refresh_token),
        ttl_days=settings.jwt_refresh_token_days,
        user_agent=user_agent,
    )
    access_token = create_access_token(user["id"], user["token_version"])
    csrf_token = new_refresh_token()
    return IssuedSession(user=user, access_token=access_token, refresh_token=refresh_token, csrf_token=csrf_token)


def register(*, email: str, password: str, display_name: str, user_agent: str | None) -> IssuedSession:
    def mutator(db: dict[str, Any]) -> IssuedSession:
        if users_repo.get_user_by_email(db, email) is not None:
            raise conflict("An account with this email already exists.")
        user = users_repo.create_user(db, email=email, password_hash=hash_password(password), display_name=display_name)
        return _issue_session(db, user, user_agent=user_agent)

    return store.mutate(mutator)


def login(*, email: str, password: str, user_agent: str | None) -> IssuedSession:
    def mutator(db: dict[str, Any]) -> IssuedSession:
        user = users_repo.get_user_by_email(db, email)
        if user is None or not verify_password(password, user["password_hash"]):
            raise unauthorized("Incorrect email or password.")
        return _issue_session(db, user, user_agent=user_agent)

    return store.mutate(mutator)


def refresh(*, refresh_token: str, user_agent: str | None) -> IssuedSession:
    token_hash = hash_refresh_token(refresh_token)

    def mutator(db: dict[str, Any]) -> IssuedSession:
        existing = users_repo.get_active_refresh_session(db, token_hash)
        if existing is None:
            raise unauthorized("Session has expired or was revoked. Please log in again.")

        user = users_repo.get_user_by_id(db, existing["user_id"])
        if user is None:
            raise unauthorized("Account no longer exists.")

        # Rotate: revoke the presented refresh token and issue a brand new one.
        users_repo.revoke_refresh_session(db, existing)
        return _issue_session(db, user, user_agent=user_agent)

    return store.mutate(mutator)


def logout(*, refresh_token: str) -> None:
    token_hash = hash_refresh_token(refresh_token)

    def mutator(db: dict[str, Any]) -> None:
        existing = users_repo.get_active_refresh_session(db, token_hash)
        if existing is not None:
            users_repo.revoke_refresh_session(db, existing)

    store.mutate(mutator)
