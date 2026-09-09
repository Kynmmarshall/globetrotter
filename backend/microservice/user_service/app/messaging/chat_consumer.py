"""Consumes chat.* events from RabbitMQ and fans them out to this instance's
locally connected WebSocket clients.

An exclusive, auto-delete queue is used deliberately: chat history is durable
in the JSON store (see app/repositories/chat.py), so a queue does not need to
survive this instance restarting -- a reconnecting client recovers any missed
messages via ChatMessage.sequence, not via broker replay.
"""

from __future__ import annotations

import json
import logging

import aio_pika

from app.chat.manager import manager
from app.messaging import rabbitmq

logger = logging.getLogger(__name__)

CHAT_ROUTING_KEYS = ("chat.message.created.v1", "chat.message.hidden.v1")


async def run_chat_consumer(connection: aio_pika.abc.AbstractRobustConnection) -> None:
    channel = await connection.channel()
    exchange = await rabbitmq.declare_events_exchange(channel)
    queue = await channel.declare_queue(exclusive=True, auto_delete=True)
    for routing_key in CHAT_ROUTING_KEYS:
        await queue.bind(exchange, routing_key=routing_key)

    async with queue.iterator() as messages:
        async for message in messages:
            async with message.process():
                try:
                    payload = json.loads(message.body.decode("utf-8"))
                    await manager.broadcast({"type": payload.get("event_type", "chat.event"), "data": payload})
                except Exception:
                    logger.exception("Failed to forward chat event to local WebSocket clients")
