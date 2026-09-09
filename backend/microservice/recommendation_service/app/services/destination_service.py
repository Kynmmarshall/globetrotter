"""Destination catalogue: search, detail, and seeding from the shared JSON file."""

from __future__ import annotations

import json
import logging
from typing import Any

from app.core.config import settings
from app.core.errors import not_found
from app.models import Destination
from app.repositories import destinations as destinations_repo
from app.repositories import outbox as outbox_repo
from app.store import store

logger = logging.getLogger(__name__)


def get_destination(destination_id: str) -> Destination:
    destination = destinations_repo.get_by_id(store.read(), destination_id)
    if destination is None:
        raise not_found(f"No destination with id {destination_id!r}.")
    return destination


def search_destinations(*, query: str | None, category: str | None, limit: int, offset: int) -> tuple[list[Destination], int]:
    return destinations_repo.search(store.read(), query=query, category=category, limit=limit, offset=offset)


def _row_fields(entry: dict) -> dict:
    return {
        "slug": entry["slug"],
        "name": entry["name"],
        "category": entry["category"],
        "lat": entry["lat"],
        "lng": entry["lng"],
        "tags": entry.get("tags", []),
        "description": entry["description"],
        "city": entry["city"],
        "country": entry["country"],
        "currency": entry["currency"],
        "timezone": entry["timezone"],
        "image": entry["image"],
    }


def seed_from_json() -> int:
    """Idempotent upsert of the canonical destination catalogue.

    Safe to call on every startup: unchanged rows are left alone (and don't
    enqueue an event); rows that are new or actually changed are upserted and
    get a destination.updated.v1 outbox event so the Itinerary Service can
    refresh its display snapshots.
    """
    if not settings.seed_destinations_file.exists():
        logger.warning("Seed file not found, skipping: %s", settings.seed_destinations_file)
        return 0

    entries = json.loads(settings.seed_destinations_file.read_text(encoding="utf-8"))

    def mutator(db: dict[str, Any]) -> int:
        changed_count = 0
        for entry in entries:
            row, changed = destinations_repo.upsert(db, destination_id=entry["id"], fields=_row_fields(entry))
            if changed:
                changed_count += 1
                outbox_repo.enqueue_event(
                    db,
                    event_type="destination.updated.v1",
                    aggregate_type="destination",
                    aggregate_id=row["id"],
                    payload={
                        "destination_id": row["id"],
                        "name": row["name"],
                        "image": row["image"],
                        "lat": row["lat"],
                        "lng": row["lng"],
                    },
                )
        return changed_count

    changed_count = store.mutate(mutator)
    logger.info("Seeded %d destinations (%d new/changed).", len(entries), changed_count)
    return changed_count
