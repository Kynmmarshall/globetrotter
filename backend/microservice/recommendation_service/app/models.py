"""Typed shapes of the JSON records stored by app/store.py (see that module's
and the User Service's app/models.py docstrings for the general rationale).
"""

from __future__ import annotations

from typing import TypedDict


class Destination(TypedDict):
    id: str
    slug: str
    name: str
    category: str
    lat: float
    lng: float
    tags: list[str]
    description: str
    city: str
    country: str
    currency: str
    timezone: str
    image: dict
    created_at: str
    updated_at: str


class UserPreferenceProjection(TypedDict):
    """Local read model of a User Service user's preferences and favourites."""

    user_id: str
    interests: list[str]
    budget_band: str | None
    pace: str | None
    accessibility_needs: list[str]
    favourite_destination_ids: list[str]
    updated_at: str


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
    """Idempotency guard for consumed events (user.preferences.updated.v1, etc.)."""

    event_id: str
    processed_at: str
