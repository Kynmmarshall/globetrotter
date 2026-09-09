"""Pydantic request/response schemas for the User Service API."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

# --- Auth -------------------------------------------------------------------


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=80)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    csrf_token: str


# --- Preferences / profile ---------------------------------------------------


class Preferences(BaseModel):
    interests: list[str] = Field(default_factory=list, max_length=20)
    budget_band: Literal["low", "medium", "high"] | None = None
    pace: Literal["relaxed", "balanced", "packed"] | None = None
    accessibility_needs: list[str] = Field(default_factory=list, max_length=20)
    starting_area: str | None = Field(default=None, max_length=120)


class UserProfile(BaseModel):
    id: str
    email: EmailStr
    display_name: str
    bio: str | None
    home_city: str | None
    avatar_url: str | None
    locale: str
    preferences: Preferences
    favourite_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=80)
    bio: str | None = Field(default=None, max_length=500)
    home_city: str | None = Field(default=None, max_length=120)
    locale: str | None = Field(default=None, max_length=10)


class UpdatePreferencesRequest(Preferences):
    pass


# --- Favourites ---------------------------------------------------------------


class FavouriteRequest(BaseModel):
    destination_id: str = Field(min_length=1, max_length=80)


class FavouriteResponse(BaseModel):
    destination_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Chat ---------------------------------------------------------------------


class ChatSendRequest(BaseModel):
    client_message_id: str = Field(min_length=1, max_length=64)
    text: str = Field(min_length=1, max_length=1000)


class ChatMessageResponse(BaseModel):
    id: str
    room_id: str
    sequence: int
    sender_id: str
    sender_display_name: str
    text: str
    created_at: datetime
    hidden: bool


class ChatHistoryResponse(BaseModel):
    messages: list[ChatMessageResponse]
    next_before_sequence: int | None


class ChatReportRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=255)
