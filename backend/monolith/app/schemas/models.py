from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=80)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserPublic(BaseModel):
    id: str
    email: EmailStr
    display_name: str
    home_city: str | None = None
    interests: list[str] = Field(default_factory=list)
    created_at: datetime


class DestinationImageVariant(BaseModel):
    width: int
    height: int
    path: str


class DestinationImage(BaseModel):
    alt: str
    primary: str
    variants: list[DestinationImageVariant]


class Destination(BaseModel):
    id: str
    slug: str
    name: str
    category: str
    city: str
    country: str
    lat: float
    lng: float
    tags: list[str] = Field(default_factory=list)
    description: str
    image: DestinationImage


class RecommendedDestination(BaseModel):
    destination: Destination
    reason: str
    score: float


class ItineraryItemCreate(BaseModel):
    destination_id: str
    day: int = Field(ge=1)
    position: int = Field(ge=0)
    notes: str | None = Field(default=None, max_length=500)


class ItineraryItem(ItineraryItemCreate):
    destination: Destination


class ItineraryCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    start_date: date
    end_date: date
    items: list[ItineraryItemCreate] = Field(default_factory=list)


class Itinerary(BaseModel):
    id: str
    owner_id: str
    title: str
    start_date: date
    end_date: date
    items: list[ItineraryItem]
    created_at: datetime
    updated_at: datetime
