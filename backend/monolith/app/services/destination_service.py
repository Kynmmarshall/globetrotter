from __future__ import annotations

from app.repositories.json_store import store
from app.schemas.models import Destination


async def list_destinations(search: str | None, category: str | None) -> list[Destination]:
    db = await store.read()
    items = db["destinations"]

    if category:
        items = [d for d in items if d["category"] == category]

    if search:
        needle = search.strip().lower()
        items = [
            d
            for d in items
            if needle in d["name"].lower()
            or needle in d["description"].lower()
            or any(needle in tag.lower() for tag in d.get("tags", []))
        ]

    return [Destination.model_validate(d) for d in items]


async def get_destination(destination_id: str) -> Destination | None:
    db = await store.read()
    match = next((d for d in db["destinations"] if d["id"] == destination_id), None)
    return Destination.model_validate(match) if match else None
