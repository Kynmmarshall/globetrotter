"""RabbitMQ connection helpers shared by the outbox publisher and chat consumer.

One durable topic exchange ("globetrotter.events") carries every domain event
in this system. Consumers bind their own named/durable queue (for reliable,
at-least-once cross-service processing) or a temporary auto-delete queue (for
this-instance-only live fan-out, e.g. chat) to the routing keys they care
about.
"""

from __future__ import annotations

import aio_pika

from app.core.config import settings

EXCHANGE_NAME = "globetrotter.events"


async def connect() -> aio_pika.RobustConnection:
    return await aio_pika.connect_robust(settings.rabbitmq_url)


async def declare_events_exchange(channel: aio_pika.abc.AbstractChannel) -> aio_pika.abc.AbstractExchange:
    return await channel.declare_exchange(EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True)
