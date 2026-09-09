"""Public, read-only, no-authentication itinerary view via a share token."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.models import PublicItineraryItemResponse, PublicItineraryResponse
from app.services import itinerary_service

router = APIRouter(prefix="/api/v1/public/itineraries", tags=["public"])


@router.get("/{token}", response_model=PublicItineraryResponse)
def get_public_itinerary(token: str) -> PublicItineraryResponse:
    itinerary, items = itinerary_service.get_public_itinerary(token)
    return PublicItineraryResponse(
        title=itinerary["title"],
        start_date=itinerary["start_date"],
        end_date=itinerary["end_date"],
        currency=itinerary["currency"],
        items=[
            PublicItineraryItemResponse(
                day=item["day"],
                position=item["position"],
                scheduled_time=item["scheduled_time"],
                duration_minutes=item["duration_minutes"],
                destination_snapshot=item["destination_snapshot"],
            )
            for item in items
        ],
    )
