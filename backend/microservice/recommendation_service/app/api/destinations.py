"""Destination catalogue endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.schemas.models import DestinationListResponse, DestinationResponse
from app.services import destination_service

router = APIRouter(prefix="/api/v1/destinations", tags=["destinations"])


@router.get("", response_model=DestinationListResponse)
def list_destinations(
    q: str | None = Query(default=None, max_length=120),
    category: str | None = Query(default=None, max_length=40),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> DestinationListResponse:
    rows, total = destination_service.search_destinations(query=q, category=category, limit=limit, offset=offset)
    return DestinationListResponse(
        items=[DestinationResponse.model_validate(row) for row in rows], total=total, limit=limit, offset=offset
    )


@router.get("/{destination_id}", response_model=DestinationResponse)
def get_destination(destination_id: str) -> DestinationResponse:
    destination = destination_service.get_destination(destination_id)
    return DestinationResponse.model_validate(destination)
