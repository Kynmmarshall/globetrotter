"""Driving directions endpoint (proxies an OSRM-compatible provider)."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.models import DirectionsRequest, DirectionsResponse
from app.services import directions_service

router = APIRouter(prefix="/api/v1/directions", tags=["directions"])


@router.post("", response_model=DirectionsResponse)
async def get_directions(payload: DirectionsRequest) -> DirectionsResponse:
    return await directions_service.get_directions(payload)
