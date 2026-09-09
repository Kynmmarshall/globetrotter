from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import itineraries, public
from app.core.config import settings
from app.core.errors import register_error_handlers
from app.messaging import rabbitmq
from app.messaging.destination_consumer import run_destination_consumer
from app.messaging.outbox_worker import run_outbox_worker

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    stop_event = asyncio.Event()
    background_tasks: list[asyncio.Task] = []
    connection = None

    try:
        connection = await rabbitmq.connect()
        background_tasks.append(asyncio.create_task(run_outbox_worker(stop_event)))
        background_tasks.append(asyncio.create_task(run_destination_consumer(connection)))
        logger.info("Connected to RabbitMQ; outbox worker and destination consumer started.")
    except Exception:
        logger.exception(
            "Could not connect to RabbitMQ at startup. The API will still serve "
            "requests, but itinerary.created/deleted.v1 won't be published and "
            "destination snapshots won't refresh until RabbitMQ is reachable."
        )

    try:
        yield
    finally:
        stop_event.set()
        for task in background_tasks:
            task.cancel()
        for task in background_tasks:
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass
        if connection is not None:
            await connection.close()


app = FastAPI(
    title="GlobeTrotter Itinerary Service",
    description="Trip planning: ordered stops, days, sharing. Phase 2 microservice.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)

app.include_router(itineraries.router)
app.include_router(public.router)


@app.get("/health", tags=["ops"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
