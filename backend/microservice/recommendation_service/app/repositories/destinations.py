"""Plain-dict access to destinations."""

from __future__ import annotations

from typing import Any

from app.models import Destination
from app.store import now_iso


def get_by_id(db: dict[str, Any], destination_id: str) -> Destination | None:
    return next((d for d in db["destinations"] if d["id"] == destination_id), None)


def upsert(db: dict[str, Any], *, destination_id: str, fields: dict) -> tuple[Destination, bool]:
    """Insert or update a destination. Returns (row, changed)."""
    existing = get_by_id(db, destination_id)
    if existing is None:
        now = now_iso()
        row: Destination = {"id": destination_id, "created_at": now, "updated_at": now, **fields}
        db["destinations"].append(row)
        return row, True

    changed = False
    for key, value in fields.items():
        if existing.get(key) != value:
            existing[key] = value
            changed = True
    if changed:
        existing["updated_at"] = now_iso()
    return existing, changed


def search(
    db: dict[str, Any], *, query: str | None, category: str | None, limit: int, offset: int
) -> tuple[list[Destination], int]:
    destinations = list(db["destinations"])

    if category:
        destinations = [d for d in destinations if d["category"] == category]

    if query:
        needle = query.lower()
        destinations = [d for d in destinations if needle in d["name"].lower() or needle in d["description"].lower()]

    destinations.sort(key=lambda d: d["name"])
    total = len(destinations)
    return destinations[offset : offset + limit], total


def list_all(db: dict[str, Any]) -> list[Destination]:
    return sorted(db["destinations"], key=lambda d: d["name"])


def get_many(db: dict[str, Any], destination_ids: list[str]) -> list[Destination]:
    wanted = set(destination_ids)
    return [d for d in db["destinations"] if d["id"] in wanted]
