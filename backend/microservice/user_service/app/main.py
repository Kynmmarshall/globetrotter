from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, chat, users
from app.core.config import settings
from app.core.errors import register_error_handlers
from app.messaging import rabbitmq
from app.messaging.chat_consumer import run_chat_consumer
from app.messaging.outbox_worker import run_outbox_worker

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    stop_event = asyncio.Event()
    background_tasks: list[asyncio.Task] = []

    try:
        chat_connection = await rabbitmq.connect()
        background_tasks.append(asyncio.create_task(run_outbox_worker(stop_event)))
        background_tasks.append(asyncio.create_task(run_chat_consumer(chat_connection)))
        logger.info("Connected to RabbitMQ; outbox worker and chat consumer started.")
    except Exception:
        chat_connection = None
        logger.exception(
            "Could not connect to RabbitMQ at startup. The API will still serve "
            "requests, but outbox events won't be published and chat won't fan "
            "out across instances until RabbitMQ is reachable."
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
        if chat_connection is not None:
            await chat_connection.close()


app = FastAPI(
    title="GlobeTrotter User Service",
    description="Auth, profile, favourites, and global chat. Phase 2 microservice.",
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

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(chat.router)
app.include_router(chat.ws_router)


@app.get("/health", tags=["ops"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
