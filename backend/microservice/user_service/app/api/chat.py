"""Chat REST history/moderation endpoints and the /ws/chat WebSocket endpoint.

Wire protocol on the WebSocket (see PROJECT_PLAN.md section 12):
  client -> server: {"type": "chat.send", "client_message_id": "...", "text": "..."}
  client -> server: {"type": "ping"}
  server -> client: {"type": "chat.message.created.v1", "data": {...}}
  server -> client: {"type": "chat.message.hidden.v1", "data": {...}}
  server -> client: {"type": "chat.ack", "client_message_id": "...", "data": {...}}
  server -> client: {"type": "error", "message": "..."}
  server -> client: {"type": "pong"}
"""

from __future__ import annotations

import json
import logging

import jwt
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from app.api.deps import get_current_user, require_csrf
from app.chat.manager import manager
from app.core.config import settings
from app.core.errors import AppError
from app.core.security import decode_access_token
from app.models import User
from app.repositories import users as users_repo
from app.schemas.models import ChatHistoryResponse, ChatMessageResponse, ChatReportRequest, ChatSendRequest
from app.services import chat_service
from app.store import store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


def _to_response(message, sender_display_name: str) -> ChatMessageResponse:
    hidden = message["hidden_at"] is not None
    return ChatMessageResponse(
        id=message["id"],
        room_id=message["room_id"],
        sequence=message["sequence"],
        sender_id=message["sender_id"],
        sender_display_name=sender_display_name,
        text="[message removed by a moderator]" if hidden else message["text"],
        created_at=message["created_at"],
        hidden=hidden,
    )


@router.get("/messages", response_model=ChatHistoryResponse)
def get_history(
    before_sequence: int | None = Query(default=None, ge=1),
    limit: int = Query(default=settings.chat_history_page_size, ge=1, le=100),
    current_user: User = Depends(get_current_user),
) -> ChatHistoryResponse:
    messages, next_before = chat_service.get_recent_history(before_sequence=before_sequence, limit=limit)
    db = store.read()
    responses = []
    for message in messages:
        sender = users_repo.get_user_by_id(db, message["sender_id"])
        responses.append(_to_response(message, sender["display_name"] if sender else "Unknown"))
    return ChatHistoryResponse(messages=responses, next_before_sequence=next_before)


@router.post("/messages/{message_id}/report", status_code=204, dependencies=[Depends(require_csrf)])
def report_message(
    message_id: str, payload: ChatReportRequest, current_user: User = Depends(get_current_user)
) -> None:
    chat_service.report_message(current_user["id"], message_id=message_id, reason=payload.reason)


@router.post("/messages/{message_id}/hide", response_model=ChatMessageResponse, dependencies=[Depends(require_csrf)])
def hide_message(
    message_id: str, payload: ChatReportRequest, current_user: User = Depends(get_current_user)
) -> ChatMessageResponse:
    message = chat_service.hide_message(current_user["id"], message_id=message_id, reason=payload.reason)
    sender = users_repo.get_user_by_id(store.read(), message["sender_id"])
    return _to_response(message, sender["display_name"] if sender else "Unknown")


def _authenticate_websocket(websocket: WebSocket) -> User | None:
    token = websocket.cookies.get(settings.access_cookie_name)
    if not token:
        auth_header = websocket.headers.get("authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header[7:]
    if not token:
        return None

    try:
        claims = decode_access_token(token)
    except jwt.PyJWTError:
        return None

    user = users_repo.get_user_by_id(store.read(), claims.get("sub", ""))
    if user is None or claims.get("tv") != user["token_version"]:
        return None
    return user


ws_router = APIRouter()


@ws_router.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket) -> None:
    # Origin allowlist: same-origin gateway connections only (see plan section 12).
    origin = websocket.headers.get("origin")
    if origin is not None and origin not in settings.cors_origins:
        await websocket.close(code=4403)
        return

    user = _authenticate_websocket(websocket)
    if user is None:
        await websocket.close(code=4401)
        return

    await manager.connect(websocket, user["id"])
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                envelope = json.loads(raw)
            except json.JSONDecodeError:
                await manager.send_to(websocket, {"type": "error", "message": "Invalid JSON."})
                continue

            message_type = envelope.get("type")
            if message_type == "ping":
                await manager.send_to(websocket, {"type": "pong"})
                continue

            if message_type == "chat.send":
                try:
                    send_request = ChatSendRequest.model_validate(envelope)
                except ValidationError as exc:
                    await manager.send_to(websocket, {"type": "error", "message": exc.errors()[0]["msg"]})
                    continue

                fresh_user = users_repo.get_user_by_id(store.read(), user["id"])
                if fresh_user is None:
                    await manager.send_to(websocket, {"type": "error", "message": "Account no longer exists."})
                    continue
                try:
                    message = chat_service.send_message(
                        fresh_user["id"],
                        client_message_id=send_request.client_message_id,
                        text=send_request.text,
                    )
                except AppError as exc:
                    await manager.send_to(websocket, {"type": "error", "message": exc.message})
                    continue
                await manager.send_to(
                    websocket,
                    {
                        "type": "chat.ack",
                        "client_message_id": send_request.client_message_id,
                        "data": _to_response(message, fresh_user["display_name"]).model_dump(mode="json"),
                    },
                )
                # The outbox worker publishes to RabbitMQ, whose consumer
                # broadcasts to every instance (including this one) so all
                # clients -- not just the sender -- receive chat.message.created.v1.
                continue

            await manager.send_to(websocket, {"type": "error", "message": f"Unknown message type: {message_type}"})
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)
