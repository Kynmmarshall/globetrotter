"""Favourite destination bookmarks."""

from __future__ import annotations

from typing import Any

from app.core.errors import not_found
from app.models import Favourite
from app.repositories import outbox as outbox_repo
from app.repositories import users as users_repo
from app.store import store


def list_favourites(user_id: str) -> list[Favourite]:
    return users_repo.list_favourites(store.read(), user_id)


def add_favourite(user_id: str, destination_id: str) -> Favourite:
    def mutator(db: dict[str, Any]) -> Favourite:
        existing = users_repo.get_favourite(db, user_id, destination_id)
        if existing is not None:
            return existing

        favourite = users_repo.add_favourite(db, user_id, destination_id)
        outbox_repo.enqueue_event(
            db,
            event_type="user.favourite.changed.v1",
            aggregate_type="user",
            aggregate_id=user_id,
            payload={"user_id": user_id, "destination_id": destination_id, "action": "added"},
        )
        return favourite

    return store.mutate(mutator)


def remove_favourite(user_id: str, destination_id: str) -> None:
    def mutator(db: dict[str, Any]) -> None:
        existing = users_repo.get_favourite(db, user_id, destination_id)
        if existing is None:
            raise not_found("That destination is not in your favourites.")

        users_repo.remove_favourite(db, existing)
        outbox_repo.enqueue_event(
            db,
            event_type="user.favourite.changed.v1",
            aggregate_type="user",
            aggregate_id=user_id,
            payload={"user_id": user_id, "destination_id": destination_id, "action": "removed"},
        )

    store.mutate(mutator)
