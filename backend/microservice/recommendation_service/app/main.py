from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import destinations, directions, recommendations
from app.core.config import settings
from app.core.errors import register_error_handlers
from app.messaging import rabbitmq
from app.messaging.outbox_worker import run_outbox_worker
from app.messaging.preference_consumer import run_preference_consumer
from app.services import destination_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        destination_service.seed_from_json()
    except Exception:
        logger.exception("Destination seed step failed; continuing with whatever data already exists.")

    stop_event = asyncio.Event()
    background_tasks: list[asyncio.Task] = []
    connection = None

    try:
        connection = await rabbitmq.connect()
        background_tasks.append(asyncio.create_task(run_outbox_worker(stop_event)))
        background_tasks.append(asyncio.create_task(run_preference_consumer(connection)))
        logger.info("Connected to RabbitMQ; outbox worker and preference consumer started.")
    except Exception:
        logger.exception(
            "Could not connect to RabbitMQ at startup. The API will still serve "
            "requests, but destination.updated.v1 won't be published and the "
            "preference projection won't stay in sync until RabbitMQ is reachable."
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
    title="GlobeTrotter Recommendation Service",
    description="Destination catalogue, recommendations, and directions. Phase 2 microservice.",
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

settings.static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")

app.include_router(destinations.router)
app.include_router(recommendations.router)
app.include_router(directions.router)


@app.get("/health", tags=["ops"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
