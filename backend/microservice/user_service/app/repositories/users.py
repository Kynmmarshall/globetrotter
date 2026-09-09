"""Plain-dict access to users, favourites, and refresh sessions.

Every function here takes the already-loaded store dict (see app/store.py)
and either reads from it or mutates it in place; callers wrap write
operations in a single `store.mutate(...)` call so a whole logical operation
(e.g. "create user" + "issue refresh session") persists atomically or not at
all -- see app/store.py's docstring for why that still holds without a real
database transaction.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.models import Favourite, RefreshSession, User
from app.store import new_id, now_iso


def get_user_by_email(db: dict[str, Any], email: str) -> User | None:
    email = email.lower()
    return next((u for u in db["users"] if u["email"] == email), None)


def get_user_by_id(db: dict[str, Any], user_id: str) -> User | None:
    return next((u for u in db["users"] if u["id"] == user_id), None)


def create_user(db: dict[str, Any], *, email: str, password_hash: str, display_name: str) -> User:
    now = now_iso()
    user: User = {
        "id": new_id(),
        "email": email.lower(),
        "password_hash": password_hash,
        "display_name": display_name,
        "bio": None,
        "home_city": None,
        "avatar_url": None,
        "locale": "en",
        "preferences": {},
        "token_version": 0,
        "is_admin": False,
        "muted_until": None,
        "created_at": now,
        "updated_at": now,
    }
    db["users"].append(user)
    return user


def create_refresh_session(
    db: dict[str, Any], *, user_id: str, token_hash: str, ttl_days: int, user_agent: str | None
) -> RefreshSession:
    expires_at = (datetime.now(timezone.utc) + timedelta(days=ttl_days)).isoformat()
    session: RefreshSession = {
        "id": new_id(),
        "user_id": user_id,
        "token_hash": token_hash,
        "user_agent": user_agent,
        "created_at": now_iso(),
        "expires_at": expires_at,
        "revoked_at": None,
    }
    db["refresh_sessions"].append(session)
    return session


def get_active_refresh_session(db: dict[str, Any], token_hash: str) -> RefreshSession | None:
    session = next((s for s in db["refresh_sessions"] if s["token_hash"] == token_hash), None)
    if session is None or session["revoked_at"] is not None:
        return None
    if datetime.fromisoformat(session["expires_at"]) <= datetime.now(timezone.utc):
        return None
    return session


def revoke_refresh_session(db: dict[str, Any], session: RefreshSession) -> None:
    session["revoked_at"] = now_iso()


def list_favourites(db: dict[str, Any], user_id: str) -> list[Favourite]:
    favourites = [f for f in db["favourites"] if f["user_id"] == user_id]
    favourites.sort(key=lambda f: f["created_at"])
    return favourites


def get_favourite(db: dict[str, Any], user_id: str, destination_id: str) -> Favourite | None:
    return next(
        (f for f in db["favourites"] if f["user_id"] == user_id and f["destination_id"] == destination_id), None
    )


def add_favourite(db: dict[str, Any], user_id: str, destination_id: str) -> Favourite:
    favourite: Favourite = {
        "id": new_id(),
        "user_id": user_id,
        "destination_id": destination_id,
        "created_at": now_iso(),
    }
    db["favourites"].append(favourite)
    return favourite


def remove_favourite(db: dict[str, Any], favourite: Favourite) -> None:
    db["favourites"].remove(favourite)
