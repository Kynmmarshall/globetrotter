"""Plain-dict access to chat messages, sequencing, and reports."""

from __future__ import annotations

from typing import Any

from app.models import ChatMessage, ChatReport
from app.store import new_id, now_iso


def _next_sequence(db: dict[str, Any], room_id: str) -> int:
    """Allocate the next per-room sequence number. Only ever called from
    inside a store.mutate() call, so this increment-and-store is atomic with
    the message insert that follows it in the same mutator.
    """
    counters: dict[str, int] = db["room_sequence_counters"]
    next_value = counters.get(room_id, 0) + 1
    counters[room_id] = next_value
    return next_value


def get_message_by_client_id(db: dict[str, Any], sender_id: str, client_message_id: str) -> ChatMessage | None:
    return next(
        (
            m
            for m in db["chat_messages"]
            if m["sender_id"] == sender_id and m["client_message_id"] == client_message_id
        ),
        None,
    )


def create_message(db: dict[str, Any], *, room_id: str, sender_id: str, client_message_id: str, text: str) -> ChatMessage:
    """Idempotent: retrying the same (sender_id, client_message_id) returns the original row."""
    existing = get_message_by_client_id(db, sender_id, client_message_id)
    if existing is not None:
        return existing

    message: ChatMessage = {
        "id": new_id(),
        "room_id": room_id,
        "sequence": _next_sequence(db, room_id),
        "sender_id": sender_id,
        "client_message_id": client_message_id,
        "text": text,
        "created_at": now_iso(),
        "hidden_at": None,
        "hidden_reason": None,
    }
    db["chat_messages"].append(message)
    return message


def list_recent_messages(db: dict[str, Any], room_id: str, *, before_sequence: int | None, limit: int) -> list[ChatMessage]:
    messages = [m for m in db["chat_messages"] if m["room_id"] == room_id]
    if before_sequence is not None:
        messages = [m for m in messages if m["sequence"] < before_sequence]
    messages.sort(key=lambda m: m["sequence"], reverse=True)
    page = messages[:limit]
    page.reverse()
    return page


def list_messages_after(db: dict[str, Any], room_id: str, *, after_sequence: int, limit: int) -> list[ChatMessage]:
    messages = [m for m in db["chat_messages"] if m["room_id"] == room_id and m["sequence"] > after_sequence]
    messages.sort(key=lambda m: m["sequence"])
    return messages[:limit]


def get_message(db: dict[str, Any], message_id: str) -> ChatMessage | None:
    return next((m for m in db["chat_messages"] if m["id"] == message_id), None)


def hide_message(db: dict[str, Any], message: ChatMessage, *, reason: str) -> None:
    message["hidden_at"] = now_iso()
    message["hidden_reason"] = reason


def create_report(db: dict[str, Any], *, message_id: str, reporter_id: str, reason: str) -> ChatReport:
    report: ChatReport = {
        "id": new_id(),
        "message_id": message_id,
        "reporter_id": reporter_id,
        "reason": reason,
        "created_at": now_iso(),
    }
    db["chat_reports"].append(report)
    return report
