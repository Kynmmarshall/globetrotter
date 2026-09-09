"""Consumes user.preferences.updated.v1 / user.favourite.changed.v1 from
RabbitMQ and applies them to the local read-projection.

Uses a durable, named queue (unlike chat's exclusive/auto-delete queue):
these events must be processed reliably even if this service is briefly
down, not just fanned out to whichever instances happen to be connected.
Idempotency is enforced via ProcessedEvent (event_id), since RabbitMQ only
guarantees at-least-once delivery.

Simplification: a message that keeps failing is nacked with requeue=True
indefinitely (no dead-letter queue configured yet). Acceptable for this
project's scope; a production deployment should add a DLQ with a retry cap.
"""

from __future__ import annotations

import json
import logging

import aio_pika
import anyio

from app.messaging import rabbitmq
from app.repositories import preferences as preferences_repo
from app.store import store

logger = logging.getLogger(__name__)

QUEUE_NAME = "recommendation.user_events"
ROUTING_KEYS = ("user.preferences.updated.v1", "user.favourite.changed.v1")


def _apply_event(event_id: str, event_type: str, payload: dict) -> None:
    def mutator(db: dict) -> None:
        if preferences_repo.already_processed(db, event_id):
            return

        if event_type == "user.preferences.updated.v1":
            preferences_repo.upsert_preferences(
                db, user_id=payload["user_id"], preferences=payload.get("preferences", {})
            )
        elif event_type == "user.favourite.changed.v1":
            preferences_repo.apply_favourite_change(
                db, user_id=payload["user_id"], destination_id=payload["destination_id"], action=payload["action"]
            )
        else:
            logger.warning("Ignoring unknown event type on user-events queue: %s", event_type)

        preferences_repo.mark_processed(db, event_id)

    store.mutate(mutator)


async def run_preference_consumer(connection: aio_pika.abc.AbstractRobustConnection) -> None:
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=10)
    exchange = await rabbitmq.declare_events_exchange(channel)
    queue = await channel.declare_queue(QUEUE_NAME, durable=True)
    for routing_key in ROUTING_KEYS:
        await queue.bind(exchange, routing_key=routing_key)

    async with queue.iterator() as messages:
        async for message in messages:
            try:
                payload = json.loads(message.body.decode("utf-8"))
                event_id = payload.get("event_id", "")
                event_type = payload.get("event_type", message.routing_key or "")
                await anyio.to_thread.run_sync(_apply_event, event_id, event_type, payload)
                await message.ack()
            except Exception:
                logger.exception("Failed to process user-event message; requeuing")
                await message.nack(requeue=True)
