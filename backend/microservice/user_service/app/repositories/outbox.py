"""Plain-dict access to the transactional outbox."""

from __future__ import annotations

from typing import Any

from app.models import OutboxEvent
from app.store import new_id, now_iso


def enqueue_event(db: dict[str, Any], *, event_type: str, aggregate_type: str, aggregate_id: str, payload: dict) -> OutboxEvent:
    event: OutboxEvent = {
        "id": new_id(),
        "event_type": event_type,
        "aggregate_type": aggregate_type,
        "aggregate_id": aggregate_id,
        "payload": payload,
        "created_at": now_iso(),
        "published_at": None,
        "attempts": 0,
    }
    db["outbox_events"].append(event)
    return event


def list_unpublished(db: dict[str, Any], limit: int = 50) -> list[OutboxEvent]:
    events = [e for e in db["outbox_events"] if e["published_at"] is None]
    events.sort(key=lambda e: e["created_at"])
    return events[:limit]


def get_by_id(db: dict[str, Any], event_id: str) -> OutboxEvent | None:
    return next((e for e in db["outbox_events"] if e["id"] == event_id), None)


def mark_published(db: dict[str, Any], event: OutboxEvent) -> None:
    event["published_at"] = now_iso()


def mark_attempt_failed(db: dict[str, Any], event: OutboxEvent) -> None:
    event["attempts"] += 1
