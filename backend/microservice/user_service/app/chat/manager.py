"""In-process registry of live chat WebSocket connections for THIS instance.

Cross-instance fan-out happens via RabbitMQ (see
app/messaging/chat_consumer.py): every instance's consumer calls
ConnectionManager.broadcast() for messages published by any instance,
including its own, so a single code path handles both cases.
"""

from __future__ import annotations

import json
import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        await websocket.accept()
        self._connections[websocket] = user_id

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.pop(websocket, None)

    async def broadcast(self, message: dict) -> None:
        body = json.dumps(message)
        dead: list[WebSocket] = []
        for websocket in list(self._connections):
            try:
                await websocket.send_text(body)
            except Exception:
                dead.append(websocket)
        for websocket in dead:
            self.disconnect(websocket)

    async def send_to(self, websocket: WebSocket, message: dict) -> None:
        await websocket.send_text(json.dumps(message))

    @property
    def connection_count(self) -> int:
        return len(self._connections)


manager = ConnectionManager()
