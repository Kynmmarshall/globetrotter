from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_id
from app.schemas.models import Itinerary, ItineraryCreate
from app.services import itinerary_service

router = APIRouter(prefix="/itineraries", tags=["itineraries"])


@router.post("", response_model=Itinerary, status_code=201)
async def create_itinerary(
    payload: ItineraryCreate,
    user_id: str = Depends(get_current_user_id),
) -> Itinerary:
    return await itinerary_service.create_itinerary(user_id, payload)


@router.get("", response_model=list[Itinerary])
async def list_itineraries(user_id: str = Depends(get_current_user_id)) -> list[Itinerary]:
    return await itinerary_service.list_itineraries_for_owner(user_id)


@router.get("/{itinerary_id}", response_model=Itinerary)
async def get_itinerary(
    itinerary_id: str,
    user_id: str = Depends(get_current_user_id),
) -> Itinerary:
    return await itinerary_service.get_itinerary_for_owner(user_id, itinerary_id)
