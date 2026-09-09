"""Plain-dict access to itinerary items (ordered stops)."""

from __future__ import annotations

from typing import Any

from app.models import ItineraryItem
from app.store import new_id, now_iso


def get(db: dict[str, Any], itinerary_id: str, item_id: str) -> ItineraryItem | None:
    return next(
        (i for i in db["itinerary_items"] if i["id"] == item_id and i["itinerary_id"] == itinerary_id), None
    )


def next_position(db: dict[str, Any], itinerary_id: str, day: int) -> int:
    positions = [
        i["position"] for i in db["itinerary_items"] if i["itinerary_id"] == itinerary_id and i["day"] == day
    ]
    return (max(positions) if positions else 0) + 1


def create(
    db: dict[str, Any],
    *,
    itinerary_id: str,
    destination_id: str,
    day: int,
    scheduled_time: str | None,
    duration_minutes: int | None,
    notes: str | None,
    estimated_cost: float | None,
    destination_snapshot: dict,
) -> ItineraryItem:
    now = now_iso()
    item: ItineraryItem = {
        "id": new_id(),
        "itinerary_id": itinerary_id,
        "destination_id": destination_id,
        "day": day,
        "position": next_position(db, itinerary_id, day),
        "scheduled_time": scheduled_time,
        "duration_minutes": duration_minutes,
        "notes": notes,
        "estimated_cost": estimated_cost,
        "destination_snapshot": destination_snapshot,
        "created_at": now,
        "updated_at": now,
    }
    db["itinerary_items"].append(item)
    return item


def delete(db: dict[str, Any], item: ItineraryItem) -> None:
    db["itinerary_items"].remove(item)


def move(db: dict[str, Any], item: ItineraryItem, *, direction: str) -> None:
    """Swap this item's position with its neighbour within the same day.

    Plain in-memory dicts, so (unlike the earlier SQL version) there is no
    unique-constraint hazard from writing both new positions in one go.
    """
    siblings = [
        i
        for i in db["itinerary_items"]
        if i["itinerary_id"] == item["itinerary_id"] and i["day"] == item["day"]
    ]
    siblings.sort(key=lambda i: i["position"])
    index = next(idx for idx, sibling in enumerate(siblings) if sibling["id"] == item["id"])

    neighbour_index = index - 1 if direction == "up" else index + 1
    if neighbour_index < 0 or neighbour_index >= len(siblings):
        return  # already at the edge; no-op

    neighbour = siblings[neighbour_index]
    item["position"], neighbour["position"] = neighbour["position"], item["position"]
    item["updated_at"] = now_iso()
    neighbour["updated_at"] = now_iso()


def refresh_snapshots_for_destination(db: dict[str, Any], destination_id: str, snapshot: dict) -> int:
    items = [i for i in db["itinerary_items"] if i["destination_id"] == destination_id]
    for item in items:
        item["destination_snapshot"] = snapshot
        item["updated_at"] = now_iso()
    return len(items)
