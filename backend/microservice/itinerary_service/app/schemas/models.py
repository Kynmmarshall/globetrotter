"""Pydantic request/response schemas for the Itinerary Service API."""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class DestinationSnapshot(BaseModel):
    destination_id: str
    name: str
    category: str
    lat: float
    lng: float
    image: dict


class ItineraryItemResponse(BaseModel):
    id: str
    destination_id: str
    day: int
    position: int
    scheduled_time: time | None
    duration_minutes: int | None
    notes: str | None
    estimated_cost: float | None
    destination_snapshot: DestinationSnapshot
    created_at: datetime

    model_config = {"from_attributes": True}


class ItineraryItemCreateRequest(BaseModel):
    destination_id: str = Field(min_length=1, max_length=80)
    day: int = Field(ge=1, le=60)
    scheduled_time: time | None = None
    duration_minutes: int | None = Field(default=None, ge=1, le=1440)
    notes: str | None = Field(default=None, max_length=1000)
    estimated_cost: float | None = Field(default=None, ge=0)


class ItineraryItemUpdateRequest(BaseModel):
    day: int | None = Field(default=None, ge=1, le=60)
    scheduled_time: time | None = None
    duration_minutes: int | None = Field(default=None, ge=1, le=1440)
    notes: str | None = Field(default=None, max_length=1000)
    estimated_cost: float | None = Field(default=None, ge=0)


class MoveItemRequest(BaseModel):
    direction: Literal["up", "down"]


class ItinerarySummary(BaseModel):
    id: str
    title: str
    start_date: date
    end_date: date
    currency: str
    item_count: int
    is_shared: bool
    created_at: datetime


class ItineraryResponse(BaseModel):
    id: str
    owner_id: str
    title: str
    start_date: date
    end_date: date
    currency: str
    revision: int
    items: list[ItineraryItemResponse]
    share_token: str | None
    created_at: datetime
    updated_at: datetime


class ItineraryCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    start_date: date
    end_date: date
    currency: str = Field(default="XAF", min_length=3, max_length=10)

    @model_validator(mode="after")
    def _end_not_before_start(self) -> "ItineraryCreateRequest":
        if self.end_date < self.start_date:
            raise ValueError("end_date must not be before start_date.")
        return self


class ItineraryUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=150)
    start_date: date | None = None
    end_date: date | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=10)


class ShareLinkResponse(BaseModel):
    token: str
    revoked: bool


class PublicItineraryItemResponse(BaseModel):
    day: int
    position: int
    scheduled_time: time | None
    duration_minutes: int | None
    destination_snapshot: DestinationSnapshot


class PublicItineraryResponse(BaseModel):
    title: str
    start_date: date
    end_date: date
    currency: str
    items: list[PublicItineraryItemResponse]
