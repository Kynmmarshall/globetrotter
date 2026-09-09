"""Pydantic request/response schemas for the Recommendation Service API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ImageVariant(BaseModel):
    width: int
    height: int
    path: str


class DestinationImage(BaseModel):
    alt: str
    primary: str
    variants: list[ImageVariant]


class DestinationResponse(BaseModel):
    id: str
    slug: str
    name: str
    category: str
    lat: float
    lng: float
    tags: list[str]
    description: str
    city: str
    country: str
    currency: str
    timezone: str
    image: DestinationImage

    model_config = {"from_attributes": True}


class DestinationListResponse(BaseModel):
    items: list[DestinationResponse]
    total: int
    limit: int
    offset: int


class RecommendationItem(BaseModel):
    destination: DestinationResponse
    reason: str


class RecommendationListResponse(BaseModel):
    items: list[RecommendationItem]
    personalized: bool


# --- Directions ---------------------------------------------------------------


class LatLng(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class Waypoint(BaseModel):
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    destination_id: str | None = None

    @model_validator(mode="after")
    def _one_of_coords_or_destination(self) -> "Waypoint":
        has_coords = self.lat is not None and self.lng is not None
        has_destination = self.destination_id is not None
        if has_coords == has_destination:
            raise ValueError("Provide exactly one of (lat and lng) or destination_id per waypoint.")
        return self


class DirectionsRequest(BaseModel):
    profile: Literal["driving"] = "driving"
    start: Waypoint
    stops: list[Waypoint] = Field(min_length=1)


class RouteStep(BaseModel):
    instruction: str
    distance_meters: float
    duration_seconds: float


class DirectionsResponse(BaseModel):
    profile: Literal["driving"]
    distance_meters: float
    duration_seconds: float
    geometry: list[list[float]]  # [[lng, lat], ...]
    steps: list[RouteStep]
