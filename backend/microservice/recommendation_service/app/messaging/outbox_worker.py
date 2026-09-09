"""Background worker that drains the transactional outbox to RabbitMQ.

Same pattern as the User Service's outbox worker.
"""

from __future__ import annotations

import asyncio
import json
import logging

import aio_pika
import anyio

from app.messaging import rabbitmq
from app.repositories import outbox as outbox_repo
from app.store import store

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 1.0


def _fetch_unpublished() -> list[dict]:
    return outbox_repo.list_unpublished(store.read(), limit=50)


def _mark_published(event_id: str) -> None:
    def mutator(db: dict) -> None:
        event = outbox_repo.get_by_id(db, event_id)
        if event is not None:
            outbox_repo.mark_published(db, event)

    store.mutate(mutator)


def _mark_attempt_failed(event_id: str) -> None:
    def mutator(db: dict) -> None:
        event = outbox_repo.get_by_id(db, event_id)
        if event is not None:
            outbox_repo.mark_attempt_failed(db, event)

    store.mutate(mutator)


async def _publish_pending(exchange: aio_pika.abc.AbstractExchange) -> None:
    events = await anyio.to_thread.run_sync(_fetch_unpublished)
    for event in events:
        body = json.dumps(
            {"event_id": event["id"], "event_type": event["event_type"], "occurred_at": event["created_at"], **event["payload"]}
        ).encode("utf-8")
        try:
            await exchange.publish(
                aio_pika.Message(body=body, content_type="application/json", delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
                routing_key=event["event_type"],
            )
            await anyio.to_thread.run_sync(_mark_published, event["id"])
        except Exception:
            logger.exception("Failed to publish outbox event %s (%s)", event["id"], event["event_type"])
            await anyio.to_thread.run_sync(_mark_attempt_failed, event["id"])


async def run_outbox_worker(stop_event: asyncio.Event) -> None:
    connection = await rabbitmq.connect()
    try:
        channel = await connection.channel()
        exchange = await rabbitmq.declare_events_exchange(channel)
        while not stop_event.is_set():
            try:
                await _publish_pending(exchange)
            except Exception:
                logger.exception("Outbox worker iteration failed; will retry")
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=POLL_INTERVAL_SECONDS)
            except asyncio.TimeoutError:
                pass
    finally:
        await connection.close()
