"""Typed shapes of the JSON records stored by app/store.py.

These are TypedDicts, not ORM models: there is no database session, no
lazy loading, no identity map. Repository functions build/return plain
dicts matching these shapes; every entry is stored under a top-level list
(or dict, for room_sequence_counters) key in the single JSON document.
Only this service reads/writes its store (see PROJECT_PLAN.md section 5:
"Service Ownership") -- no cross-service joins or foreign keys. Favourites
and chat messages reference destination/user ids as plain opaque strings.
"""

from __future__ import annotations

from typing import TypedDict


class User(TypedDict):
    id: str
    email: str
    password_hash: str
    display_name: str
    bio: str | None
    home_city: str | None
    avatar_url: str | None
    locale: str
    preferences: dict
    token_version: int
    is_admin: bool
    muted_until: str | None
    created_at: str
    updated_at: str


class Favourite(TypedDict):
    id: str
    user_id: str
    destination_id: str
    created_at: str


class RefreshSession(TypedDict):
    """One row per issued refresh token, so logout/rotation/revocation is server-authoritative."""

    id: str
    user_id: str
    token_hash: str
    user_agent: str | None
    created_at: str
    expires_at: str
    revoked_at: str | None


class ChatMessage(TypedDict):
    """Persisted global chat history -- the durable source of truth for the room.

    "sequence" is a per-room monotonically increasing counter assigned in the
    same store.mutate() call as the insert, so clients can page/recover by
    "give me everything after sequence N" without relying on wall-clock time.
    """

    id: str
    room_id: str
    sequence: int
    sender_id: str
    # Client-generated idempotency key: reconnect retries of the same send
    # don't create duplicate messages (see plan section 12).
    client_message_id: str
    text: str
    created_at: str
    hidden_at: str | None
    hidden_reason: str | None


class ChatReport(TypedDict):
    id: str
    message_id: str
    reporter_id: str
    reason: str
    created_at: str


class OutboxEvent(TypedDict):
    """Transactional outbox: written in the same store.mutate() call as the domain change.

    A separate publisher worker (app/messaging/outbox_worker.py) drains
    entries with published_at is None and sends them to RabbitMQ with
    publisher confirms, so a broker outage delays delivery instead of losing
    the event.
    """

    id: str
    event_type: str
    aggregate_type: str
    aggregate_id: str
    payload: dict
    created_at: str
    published_at: str | None
    attempts: int

