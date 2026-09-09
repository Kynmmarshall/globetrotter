"""Plain-dict access to the local user-preference projection."""

from __future__ import annotations

from typing import Any

from app.models import ProcessedEvent, UserPreferenceProjection
from app.store import now_iso


def get_projection(db: dict[str, Any], user_id: str) -> UserPreferenceProjection | None:
    return next((p for p in db["user_preference_projections"] if p["user_id"] == user_id), None)


def _get_or_create(db: dict[str, Any], user_id: str) -> UserPreferenceProjection:
    row = get_projection(db, user_id)
    if row is None:
        row = {
            "user_id": user_id,
            "interests": [],
            "budget_band": None,
            "pace": None,
            "accessibility_needs": [],
            "favourite_destination_ids": [],
            "updated_at": now_iso(),
        }
        db["user_preference_projections"].append(row)
    return row


def upsert_preferences(db: dict[str, Any], *, user_id: str, preferences: dict) -> UserPreferenceProjection:
    row = _get_or_create(db, user_id)
    row["interests"] = preferences.get("interests", [])
    row["budget_band"] = preferences.get("budget_band")
    row["pace"] = preferences.get("pace")
    row["accessibility_needs"] = preferences.get("accessibility_needs", [])
    row["updated_at"] = now_iso()
    return row


def apply_favourite_change(db: dict[str, Any], *, user_id: str, destination_id: str, action: str) -> UserPreferenceProjection:
    row = _get_or_create(db, user_id)
    current = set(row["favourite_destination_ids"])
    if action == "added":
        current.add(destination_id)
    else:
        current.discard(destination_id)
    row["favourite_destination_ids"] = sorted(current)
    row["updated_at"] = now_iso()
    return row


def already_processed(db: dict[str, Any], event_id: str) -> bool:
    return any(p["event_id"] == event_id for p in db["processed_events"])


def mark_processed(db: dict[str, Any], event_id: str) -> None:
    entry: ProcessedEvent = {"event_id": event_id, "processed_at": now_iso()}
    db["processed_events"].append(entry)
