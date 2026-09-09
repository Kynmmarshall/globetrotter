"""Typed shapes of the JSON records stored by app/store.py (see that module's
and the User Service's app/models.py docstrings for the general rationale).

destination_snapshot on ItineraryItem is a denormalized COPY of display data
from the Recommendation Service (name, image, lat/lng, category) taken when
the item is added and refreshed via destination.updated.v1 events -- not a
foreign key or cross-service join (see PROJECT_PLAN.md section 5/7). This is
what keeps existing trips readable even when Recommendation Service is down.
"""

from __future__ import annotations

from typing import TypedDict


class Itinerary(TypedDict):
    id: str
    owner_id: str
    title: str
    start_date: str
    end_date: str
    currency: str
    revision: int
    created_at: str
    updated_at: str


class ItineraryItem(TypedDict):
    id: str
    itinerary_id: str
    destination_id: str
    day: int
    position: int
    scheduled_time: str | None
    duration_minutes: int | None
    notes: str | None
    estimated_cost: float | None
    destination_snapshot: dict
    created_at: str
    updated_at: str


class ShareLink(TypedDict):
    id: str
    itinerary_id: str
    token: str
    created_at: str
    revoked_at: str | None


class OutboxEvent(TypedDict):
    id: str
    event_type: str
    aggregate_type: str
    aggregate_id: str
    payload: dict
    created_at: str
    published_at: str | None
    attempts: int


class ProcessedEvent(TypedDict):
    """Idempotency guard for consumed events (destination.updated.v1)."""

    event_id: str
    processed_at: str
