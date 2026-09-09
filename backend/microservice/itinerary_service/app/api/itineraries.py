"""Itinerary CRUD, ordered stops, and sharing endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user_id
from app.models import Itinerary
from app.schemas.models import (
    ItineraryCreateRequest,
    ItineraryItemCreateRequest,
    ItineraryItemResponse,
    ItineraryItemUpdateRequest,
    ItineraryResponse,
    ItinerarySummary,
    ItineraryUpdateRequest,
    MoveItemRequest,
    ShareLinkResponse,
)
from app.services import itinerary_service

router = APIRouter(prefix="/api/v1/itineraries", tags=["itineraries"])


def _to_summary(itinerary: Itinerary) -> ItinerarySummary:
    items = itinerary_service.get_items(itinerary["id"])
    share = itinerary_service.get_share(itinerary["id"])
    return ItinerarySummary(
        id=itinerary["id"],
        title=itinerary["title"],
        start_date=itinerary["start_date"],
        end_date=itinerary["end_date"],
        currency=itinerary["currency"],
        item_count=len(items),
        is_shared=share is not None and share["revoked_at"] is None,
        created_at=itinerary["created_at"],
    )


def _to_response(itinerary: Itinerary) -> ItineraryResponse:
    items = itinerary_service.get_items(itinerary["id"])
    share = itinerary_service.get_share(itinerary["id"])
    share_token = share["token"] if share is not None and share["revoked_at"] is None else None
    return ItineraryResponse(
        id=itinerary["id"],
        owner_id=itinerary["owner_id"],
        title=itinerary["title"],
        start_date=itinerary["start_date"],
        end_date=itinerary["end_date"],
        currency=itinerary["currency"],
        revision=itinerary["revision"],
        items=[ItineraryItemResponse.model_validate(item) for item in items],
        share_token=share_token,
        created_at=itinerary["created_at"],
        updated_at=itinerary["updated_at"],
    )


@router.get("", response_model=list[ItinerarySummary])
def list_itineraries(user_id: str = Depends(get_current_user_id)) -> list[ItinerarySummary]:
    itineraries = itinerary_service.list_itineraries(user_id)
    return [_to_summary(i) for i in itineraries]


@router.post("", response_model=ItineraryResponse, status_code=status.HTTP_201_CREATED)
def create_itinerary(payload: ItineraryCreateRequest, user_id: str = Depends(get_current_user_id)) -> ItineraryResponse:
    itinerary = itinerary_service.create_itinerary(
        user_id=user_id,
        title=payload.title,
        start_date=payload.start_date,
        end_date=payload.end_date,
        currency=payload.currency,
    )
    return _to_response(itinerary)


@router.get("/{itinerary_id}", response_model=ItineraryResponse)
def get_itinerary(itinerary_id: str, user_id: str = Depends(get_current_user_id)) -> ItineraryResponse:
    itinerary = itinerary_service.get_owned_itinerary(itinerary_id, user_id)
    return _to_response(itinerary)


@router.patch("/{itinerary_id}", response_model=ItineraryResponse)
def update_itinerary(
    itinerary_id: str, payload: ItineraryUpdateRequest, user_id: str = Depends(get_current_user_id)
) -> ItineraryResponse:
    itinerary = itinerary_service.update_itinerary(
        itinerary_id,
        user_id,
        title=payload.title,
        start_date=payload.start_date,
        end_date=payload.end_date,
        currency=payload.currency,
    )
    return _to_response(itinerary)


@router.delete("/{itinerary_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_itinerary(itinerary_id: str, user_id: str = Depends(get_current_user_id)) -> None:
    itinerary_service.delete_itinerary(itinerary_id, user_id)


@router.post("/{itinerary_id}/items", response_model=ItineraryItemResponse, status_code=status.HTTP_201_CREATED)
async def add_item(
    itinerary_id: str, payload: ItineraryItemCreateRequest, user_id: str = Depends(get_current_user_id)
) -> ItineraryItemResponse:
    item = await itinerary_service.add_item(
        itinerary_id,
        user_id,
        destination_id=payload.destination_id,
        day=payload.day,
        scheduled_time=payload.scheduled_time,
        duration_minutes=payload.duration_minutes,
        notes=payload.notes,
        estimated_cost=payload.estimated_cost,
    )
    return ItineraryItemResponse.model_validate(item)


@router.patch("/{itinerary_id}/items/{item_id}", response_model=ItineraryItemResponse)
def update_item(
    itinerary_id: str,
    item_id: str,
    payload: ItineraryItemUpdateRequest,
    user_id: str = Depends(get_current_user_id),
) -> ItineraryItemResponse:
    item = itinerary_service.update_item(
        itinerary_id,
        user_id,
        item_id,
        day=payload.day,
        scheduled_time=payload.scheduled_time,
        duration_minutes=payload.duration_minutes,
        notes=payload.notes,
        estimated_cost=payload.estimated_cost,
    )
    return ItineraryItemResponse.model_validate(item)


@router.post("/{itinerary_id}/items/{item_id}/move", response_model=ItineraryResponse)
def move_item(
    itinerary_id: str, item_id: str, payload: MoveItemRequest, user_id: str = Depends(get_current_user_id)
) -> ItineraryResponse:
    itinerary_service.move_item(itinerary_id, user_id, item_id, direction=payload.direction)
    itinerary = itinerary_service.get_owned_itinerary(itinerary_id, user_id)
    return _to_response(itinerary)


@router.delete("/{itinerary_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(itinerary_id: str, item_id: str, user_id: str = Depends(get_current_user_id)) -> None:
    itinerary_service.delete_item(itinerary_id, user_id, item_id)


@router.post("/{itinerary_id}/share", response_model=ShareLinkResponse)
def create_share(itinerary_id: str, user_id: str = Depends(get_current_user_id)) -> ShareLinkResponse:
    share = itinerary_service.create_share_link(itinerary_id, user_id)
    return ShareLinkResponse(token=share["token"], revoked=False)


@router.delete("/{itinerary_id}/share", status_code=status.HTTP_204_NO_CONTENT)
def revoke_share(itinerary_id: str, user_id: str = Depends(get_current_user_id)) -> None:
    itinerary_service.revoke_share_link(itinerary_id, user_id)
