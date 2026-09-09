"""Consumes destination.updated.v1 from RabbitMQ and refreshes stored
destination_snapshot copies on any itinerary items referencing that
destination. Durable named queue: this must be processed reliably even if
this service is briefly down (unlike chat's exclusive fan-out queue).

Simplification: a message that keeps failing is nacked with requeue=True
indefinitely (no dead-letter queue configured yet), same as the
Recommendation Service's preference consumer.
"""

from __future__ import annotations

import json
import logging

import aio_pika
import anyio

from app.messaging import rabbitmq
from app.repositories import items as items_repo
from app.repositories import outbox as outbox_repo
from app.store import store

logger = logging.getLogger(__name__)

QUEUE_NAME = "itinerary.destination_events"
ROUTING_KEY = "destination.updated.v1"


def _apply_event(event_id: str, payload: dict) -> None:
    def mutator(db: dict) -> None:
        if outbox_repo.already_processed(db, event_id):
            return

        destination_id = payload["destination_id"]
        snapshot = {
            "destination_id": destination_id,
            "name": payload["name"],
            "category": payload.get("category", ""),
            "lat": payload["lat"],
            "lng": payload["lng"],
            "image": payload["image"],
        }
        updated = items_repo.refresh_snapshots_for_destination(db, destination_id, snapshot)
        if updated:
            logger.info("Refreshed %d itinerary item snapshot(s) for destination %s", updated, destination_id)

        outbox_repo.mark_processed(db, event_id)

    store.mutate(mutator)


async def run_destination_consumer(connection: aio_pika.abc.AbstractRobustConnection) -> None:
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=10)
    exchange = await rabbitmq.declare_events_exchange(channel)
    queue = await channel.declare_queue(QUEUE_NAME, durable=True)
    await queue.bind(exchange, routing_key=ROUTING_KEY)

    async with queue.iterator() as messages:
        async for message in messages:
            try:
                payload = json.loads(message.body.decode("utf-8"))
                event_id = payload.get("event_id", "")
                await anyio.to_thread.run_sync(_apply_event, event_id, payload)
                await message.ack()
            except Exception:
                logger.exception("Failed to process destination.updated.v1 message; requeuing")
                await message.nack(requeue=True)
