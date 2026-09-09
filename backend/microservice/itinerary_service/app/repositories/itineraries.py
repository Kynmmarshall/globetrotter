"""Plain-dict access to itineraries."""

from __future__ import annotations

from typing import Any

from app.models import Itinerary, ItineraryItem, ShareLink
from app.store import new_id, now_iso


def _items_for(db: dict[str, Any], itinerary_id: str) -> list[ItineraryItem]:
    items = [i for i in db["itinerary_items"] if i["itinerary_id"] == itinerary_id]
    items.sort(key=lambda i: (i["day"], i["position"]))
    return items


def _share_for(db: dict[str, Any], itinerary_id: str) -> ShareLink | None:
    return next((s for s in db["share_links"] if s["itinerary_id"] == itinerary_id), None)


def get_by_id(db: dict[str, Any], itinerary_id: str) -> Itinerary | None:
    return next((i for i in db["itineraries"] if i["id"] == itinerary_id), None)


def get_items(db: dict[str, Any], itinerary_id: str) -> list[ItineraryItem]:
    return _items_for(db, itinerary_id)


def get_share(db: dict[str, Any], itinerary_id: str) -> ShareLink | None:
    return _share_for(db, itinerary_id)


def list_for_owner(db: dict[str, Any], owner_id: str) -> list[Itinerary]:
    itineraries = [i for i in db["itineraries"] if i["owner_id"] == owner_id]
    itineraries.sort(key=lambda i: i["start_date"], reverse=True)
    return itineraries


def create(db: dict[str, Any], *, owner_id: str, title: str, start_date: str, end_date: str, currency: str) -> Itinerary:
    now = now_iso()
    itinerary: Itinerary = {
        "id": new_id(),
        "owner_id": owner_id,
        "title": title,
        "start_date": start_date,
        "end_date": end_date,
        "currency": currency,
        "revision": 1,
        "created_at": now,
        "updated_at": now,
    }
    db["itineraries"].append(itinerary)
    return itinerary


def delete(db: dict[str, Any], itinerary: Itinerary) -> None:
    itinerary_id = itinerary["id"]
    db["itineraries"].remove(itinerary)
    db["itinerary_items"] = [i for i in db["itinerary_items"] if i["itinerary_id"] != itinerary_id]
    db["share_links"] = [s for s in db["share_links"] if s["itinerary_id"] != itinerary_id]


def touch(db: dict[str, Any], itinerary: Itinerary) -> None:
    itinerary["revision"] += 1
    itinerary["updated_at"] = now_iso()


def count_items(db: dict[str, Any], itinerary_id: str) -> int:
    return len(_items_for(db, itinerary_id))


def get_share_by_token(db: dict[str, Any], token: str) -> ShareLink | None:
    return next((s for s in db["share_links"] if s["token"] == token and s["revoked_at"] is None), None)
