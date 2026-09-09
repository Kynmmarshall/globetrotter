from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.errors import not_found
from app.schemas.models import Destination
from app.services import destination_service

router = APIRouter(prefix="/destinations", tags=["destinations"])


@router.get("", response_model=list[Destination])
async def list_destinations(
    search: str | None = Query(default=None, max_length=120),
    category: str | None = Query(default=None, max_length=40),
) -> list[Destination]:
    return await destination_service.list_destinations(search, category)


@router.get("/{destination_id}", response_model=Destination)
async def get_destination(destination_id: str) -> Destination:
    destination = await destination_service.get_destination(destination_id)
    if destination is None:
        raise not_found("Destination not found.")
    return destination
