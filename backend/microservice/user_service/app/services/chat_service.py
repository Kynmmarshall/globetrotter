"""Global chat: send, history, moderation.

Rate limiting here is a simple in-process sliding window. It is a
per-instance approximation (not shared across multiple running User Service
processes) -- adequate for the initial release; a shared Redis/RabbitMQ-backed
limiter would be needed for a strict multi-instance guarantee.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any

from app.core.errors import forbidden, too_many_requests
from app.models import ChatMessage, User
from app.repositories import chat as chat_repo
from app.repositories import outbox as outbox_repo
from app.store import store

ROOM_ID = "global"
_RATE_LIMIT_MAX_MESSAGES = 10
_RATE_LIMIT_WINDOW_SECONDS = 10.0
_send_timestamps: dict[str, deque[float]] = defaultdict(deque)


def _check_rate_limit(user_id: str) -> None:
    now = time.monotonic()
    timestamps = _send_timestamps[user_id]
    while timestamps and now - timestamps[0] > _RATE_LIMIT_WINDOW_SECONDS:
        timestamps.popleft()
    if len(timestamps) >= _RATE_LIMIT_MAX_MESSAGES:
        raise too_many_requests("You're sending messages too quickly. Please slow down.")
    timestamps.append(now)


def _is_muted(user: User) -> bool:
    if user["muted_until"] is None:
        return False
    muted_until = datetime.fromisoformat(user["muted_until"])
    if muted_until.tzinfo is None:
        muted_until = muted_until.replace(tzinfo=timezone.utc)
    return muted_until > datetime.now(timezone.utc)


def _to_payload(message: ChatMessage, sender_display_name: str) -> dict:
    return {
        "id": message["id"],
        "room_id": message["room_id"],
        "sequence": message["sequence"],
        "sender_id": message["sender_id"],
        "sender_display_name": sender_display_name,
        "text": message["text"],
        "created_at": message["created_at"],
        "hidden": message["hidden_at"] is not None,
    }


def send_message(user_id: str, *, client_message_id: str, text: str) -> ChatMessage:
    def mutator(db: dict[str, Any]) -> ChatMessage:
        user = next((u for u in db["users"] if u["id"] == user_id), None)
        if user is None:
            raise forbidden("Account no longer exists.")
        if _is_muted(user):
            raise forbidden("You are temporarily muted from chat.")
        _check_rate_limit(user_id)

        message = chat_repo.create_message(
            db, room_id=ROOM_ID, sender_id=user_id, client_message_id=client_message_id, text=text
        )

        outbox_repo.enqueue_event(
            db,
            event_type="chat.message.created.v1",
            aggregate_type="chat_message",
            aggregate_id=message["id"],
            payload=_to_payload(message, user["display_name"]),
        )
        return message

    return store.mutate(mutator)


def get_recent_history(*, before_sequence: int | None, limit: int) -> tuple[list[ChatMessage], int | None]:
    db = store.read()
    messages = chat_repo.list_recent_messages(db, ROOM_ID, before_sequence=before_sequence, limit=limit)
    next_before = messages[0]["sequence"] if len(messages) == limit else None
    return messages, next_before


def get_messages_after(*, after_sequence: int, limit: int) -> list[ChatMessage]:
    return chat_repo.list_messages_after(store.read(), ROOM_ID, after_sequence=after_sequence, limit=limit)


def hide_message(moderator_id: str, *, message_id: str, reason: str) -> ChatMessage:
    def mutator(db: dict[str, Any]) -> ChatMessage:
        moderator = next((u for u in db["users"] if u["id"] == moderator_id), None)
        if moderator is None or not moderator["is_admin"]:
            raise forbidden("Only moderators can hide messages.")

        message = chat_repo.get_message(db, message_id)
        if message is None:
            raise forbidden("Message not found.")

        chat_repo.hide_message(db, message, reason=reason)

        outbox_repo.enqueue_event(
            db,
            event_type="chat.message.hidden.v1",
            aggregate_type="chat_message",
            aggregate_id=message["id"],
            payload={"id": message["id"], "room_id": message["room_id"], "reason": reason},
        )
        return message

    return store.mutate(mutator)


def report_message(reporter_id: str, *, message_id: str, reason: str) -> None:
    def mutator(db: dict[str, Any]) -> None:
        message = chat_repo.get_message(db, message_id)
        if message is None:
            raise forbidden("Message not found.")
        chat_repo.create_report(db, message_id=message_id, reporter_id=reporter_id, reason=reason)

    store.mutate(mutator)
