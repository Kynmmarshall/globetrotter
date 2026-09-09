"""Profile and preferences updates."""

from __future__ import annotations

from typing import Any

from app.models import User
from app.repositories import outbox as outbox_repo
from app.schemas.models import Preferences, UpdatePreferencesRequest, UpdateProfileRequest
from app.store import now_iso, store


def update_profile(user_id: str, req: UpdateProfileRequest) -> User:
    def mutator(db: dict[str, Any]) -> User:
        user = next(u for u in db["users"] if u["id"] == user_id)
        if req.display_name is not None:
            user["display_name"] = req.display_name
        if req.bio is not None:
            user["bio"] = req.bio
        if req.home_city is not None:
            user["home_city"] = req.home_city
        if req.locale is not None:
            user["locale"] = req.locale
        user["updated_at"] = now_iso()
        return user

    return store.mutate(mutator)


def update_preferences(user_id: str, req: UpdatePreferencesRequest) -> User:
    def mutator(db: dict[str, Any]) -> User:
        user = next(u for u in db["users"] if u["id"] == user_id)
        preferences = Preferences.model_validate(req.model_dump())
        user["preferences"] = preferences.model_dump(mode="json")
        user["updated_at"] = now_iso()

        outbox_repo.enqueue_event(
            db,
            event_type="user.preferences.updated.v1",
            aggregate_type="user",
            aggregate_id=user["id"],
            payload={"user_id": user["id"], "preferences": user["preferences"]},
        )
        return user

    return store.mutate(mutator)
