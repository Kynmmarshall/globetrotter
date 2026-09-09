"""Itinerary CRUD, ordered stops, and sharing -- with owner authorization."""

from __future__ import annotations

from datetime import date, time
from typing import Any

from app.core.config import settings
from app.core.errors import bad_request, forbidden, not_found
from app.models import Itinerary, ItineraryItem, ShareLink
from app.repositories import itineraries as itineraries_repo
from app.repositories import items as items_repo
from app.repositories import outbox as outbox_repo
from app.repositories import shares as shares_repo
from app.services.destination_client import fetch_destination_snapshot
from app.store import now_iso, store


def _require_owner(itinerary: Itinerary, user_id: str) -> None:
    if itinerary["owner_id"] != user_id:
        raise forbidden("You do not have access to this trip.")


def get_owned_itinerary(itinerary_id: str, user_id: str) -> Itinerary:
    itinerary = itineraries_repo.get_by_id(store.read(), itinerary_id)
    if itinerary is None:
        raise not_found("Trip not found.")
    _require_owner(itinerary, user_id)
    return itinerary


def get_items(itinerary_id: str) -> list[ItineraryItem]:
    return itineraries_repo.get_items(store.read(), itinerary_id)


def get_share(itinerary_id: str) -> ShareLink | None:
    return itineraries_repo.get_share(store.read(), itinerary_id)


def list_itineraries(user_id: str) -> list[Itinerary]:
    return itineraries_repo.list_for_owner(store.read(), user_id)


def create_itinerary(*, user_id: str, title: str, start_date: date, end_date: date, currency: str) -> Itinerary:
    def mutator(db: dict[str, Any]) -> Itinerary:
        itinerary = itineraries_repo.create(
            db,
            owner_id=user_id,
            title=title,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            currency=currency,
        )
        outbox_repo.enqueue_event(
            db,
            event_type="itinerary.created.v1",
            aggregate_type="itinerary",
            aggregate_id=itinerary["id"],
            payload={"itinerary_id": itinerary["id"], "owner_id": user_id, "title": title},
        )
        return itinerary

    return store.mutate(mutator)


def update_itinerary(
    itinerary_id: str,
    user_id: str,
    *,
    title: str | None,
    start_date: date | None,
    end_date: date | None,
    currency: str | None,
) -> Itinerary:
    def mutator(db: dict[str, Any]) -> Itinerary:
        itinerary = itineraries_repo.get_by_id(db, itinerary_id)
        if itinerary is None:
            raise not_found("Trip not found.")
        _require_owner(itinerary, user_id)

        if title is not None:
            itinerary["title"] = title
        if start_date is not None:
            itinerary["start_date"] = start_date.isoformat()
        if end_date is not None:
            itinerary["end_date"] = end_date.isoformat()
        if currency is not None:
            itinerary["currency"] = currency

        if itinerary["end_date"] < itinerary["start_date"]:
            raise bad_request("end_date must not be before start_date.")

        itineraries_repo.touch(db, itinerary)
        return itinerary

    return store.mutate(mutator)


def delete_itinerary(itinerary_id: str, user_id: str) -> None:
    def mutator(db: dict[str, Any]) -> None:
        itinerary = itineraries_repo.get_by_id(db, itinerary_id)
        if itinerary is None:
            raise not_found("Trip not found.")
        _require_owner(itinerary, user_id)

        owner_id = itinerary["owner_id"]
        itineraries_repo.delete(db, itinerary)
        outbox_repo.enqueue_event(
            db,
            event_type="itinerary.deleted.v1",
            aggregate_type="itinerary",
            aggregate_id=itinerary_id,
            payload={"itinerary_id": itinerary_id, "owner_id": owner_id},
        )

    store.mutate(mutator)


async def add_item(
    itinerary_id: str,
    user_id: str,
    *,
    destination_id: str,
    day: int,
    scheduled_time: time | None,
    duration_minutes: int | None,
    notes: str | None,
    estimated_cost: float | None,
) -> ItineraryItem:
    # The destination-snapshot fetch is a real network call, so it happens
    # BEFORE acquiring the store's write lock (which is a plain, synchronous,
    # non-reentrant lock and must not be held across an await).
    itinerary = get_owned_itinerary(itinerary_id, user_id)
    if itineraries_repo.count_items(store.read(), itinerary["id"]) >= settings.max_items_per_itinerary:
        raise bad_request(f"This trip already has the maximum of {settings.max_items_per_itinerary} stops.")

    snapshot = await fetch_destination_snapshot(destination_id)

    def mutator(db: dict[str, Any]) -> ItineraryItem:
        current = itineraries_repo.get_by_id(db, itinerary_id)
        if current is None:
            raise not_found("Trip not found.")
        _require_owner(current, user_id)

        item = items_repo.create(
            db,
            itinerary_id=itinerary_id,
            destination_id=destination_id,
            day=day,
            scheduled_time=scheduled_time.isoformat() if scheduled_time else None,
            duration_minutes=duration_minutes,
            notes=notes,
            estimated_cost=estimated_cost,
            destination_snapshot=snapshot,
        )
        itineraries_repo.touch(db, current)
        return item

    return store.mutate(mutator)


def get_owned_item(itinerary_id: str, user_id: str, item_id: str) -> ItineraryItem:
    itinerary = get_owned_itinerary(itinerary_id, user_id)
    item = items_repo.get(store.read(), itinerary["id"], item_id)
    if item is None:
        raise not_found("Stop not found in this trip.")
    return item


def update_item(
    itinerary_id: str,
    user_id: str,
    item_id: str,
    *,
    day: int | None,
    scheduled_time: time | None,
    duration_minutes: int | None,
    notes: str | None,
    estimated_cost: float | None,
) -> ItineraryItem:
    def mutator(db: dict[str, Any]) -> ItineraryItem:
        itinerary = itineraries_repo.get_by_id(db, itinerary_id)
        if itinerary is None:
            raise not_found("Trip not found.")
        _require_owner(itinerary, user_id)

        item = items_repo.get(db, itinerary_id, item_id)
        if item is None:
            raise not_found("Stop not found in this trip.")

        if day is not None:
            item["day"] = day
            item["position"] = items_repo.next_position(db, itinerary_id, day)
        if scheduled_time is not None:
            item["scheduled_time"] = scheduled_time.isoformat()
        if duration_minutes is not None:
            item["duration_minutes"] = duration_minutes
        if notes is not None:
            item["notes"] = notes
        if estimated_cost is not None:
            item["estimated_cost"] = estimated_cost

        item["updated_at"] = now_iso()
        itineraries_repo.touch(db, itinerary)
        return item

    return store.mutate(mutator)


def move_item(itinerary_id: str, user_id: str, item_id: str, *, direction: str) -> None:
    def mutator(db: dict[str, Any]) -> None:
        itinerary = itineraries_repo.get_by_id(db, itinerary_id)
        if itinerary is None:
            raise not_found("Trip not found.")
        _require_owner(itinerary, user_id)

        item = items_repo.get(db, itinerary_id, item_id)
        if item is None:
            raise not_found("Stop not found in this trip.")

        items_repo.move(db, item, direction=direction)
        itineraries_repo.touch(db, itinerary)

    store.mutate(mutator)


def delete_item(itinerary_id: str, user_id: str, item_id: str) -> None:
    def mutator(db: dict[str, Any]) -> None:
        itinerary = itineraries_repo.get_by_id(db, itinerary_id)
        if itinerary is None:
            raise not_found("Trip not found.")
        _require_owner(itinerary, user_id)

        item = items_repo.get(db, itinerary_id, item_id)
        if item is None:
            raise not_found("Stop not found in this trip.")

        items_repo.delete(db, item)
        itineraries_repo.touch(db, itinerary)

    store.mutate(mutator)


def create_share_link(itinerary_id: str, user_id: str) -> ShareLink:
    def mutator(db: dict[str, Any]) -> ShareLink:
        itinerary = itineraries_repo.get_by_id(db, itinerary_id)
        if itinerary is None:
            raise not_found("Trip not found.")
        _require_owner(itinerary, user_id)

        existing = itineraries_repo.get_share(db, itinerary_id)
        return shares_repo.create_or_replace(db, itinerary_id, existing)

    return store.mutate(mutator)


def revoke_share_link(itinerary_id: str, user_id: str) -> None:
    def mutator(db: dict[str, Any]) -> None:
        itinerary = itineraries_repo.get_by_id(db, itinerary_id)
        if itinerary is None:
            raise not_found("Trip not found.")
        _require_owner(itinerary, user_id)

        existing = itineraries_repo.get_share(db, itinerary_id)
        if existing is None:
            raise not_found("This trip does not have an active share link.")
        shares_repo.revoke(db, existing)

    store.mutate(mutator)


def get_public_itinerary(token: str) -> tuple[Itinerary, list[ItineraryItem]]:
    db = store.read()
    share = itineraries_repo.get_share_by_token(db, token)
    if share is None:
        raise not_found("This share link is invalid or has been revoked.")
    itinerary = itineraries_repo.get_by_id(db, share["itinerary_id"])
    if itinerary is None:
        raise not_found("This share link is invalid or has been revoked.")
    return itinerary, itineraries_repo.get_items(db, itinerary["id"])
