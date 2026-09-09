from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.core.errors import conflict, unauthorized
from app.core.security import create_access_token, hash_password, verify_password
from app.repositories.json_store import store
from app.schemas.models import LoginRequest, RegisterRequest, TokenResponse, UserPublic


def _to_public(user: dict) -> UserPublic:
    return UserPublic(
        id=user["id"],
        email=user["email"],
        display_name=user["display_name"],
        home_city=user.get("home_city"),
        interests=user.get("interests", []),
        created_at=user["created_at"],
    )


async def register(payload: RegisterRequest) -> TokenResponse:
    def mutator(db: dict) -> dict:
        normalized_email = payload.email.lower()
        if any(u["email"] == normalized_email for u in db["users"]):
            raise conflict("An account with this email already exists.")
        user = {
            "id": f"usr-{uuid.uuid4().hex[:12]}",
            "email": normalized_email,
            "password_hash": hash_password(payload.password),
            "display_name": payload.display_name,
            "home_city": None,
            "interests": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        db["users"].append(user)
        return user

    user = await store.mutate(mutator)
    return TokenResponse(access_token=create_access_token(user["id"]))


async def login(payload: LoginRequest) -> TokenResponse:
    db = await store.read()
    normalized_email = payload.email.lower()
    user = next((u for u in db["users"] if u["email"] == normalized_email), None)
    if user is None or not verify_password(payload.password, user["password_hash"]):
        raise unauthorized("Incorrect email or password.")
    return TokenResponse(access_token=create_access_token(user["id"]))


async def get_user_or_raise(user_id: str) -> dict:
    db = await store.read()
    user = next((u for u in db["users"] if u["id"] == user_id), None)
    if user is None:
        raise unauthorized("Session refers to a user that no longer exists.")
    return user


async def get_public_user(user_id: str) -> UserPublic:
    return _to_public(await get_user_or_raise(user_id))
