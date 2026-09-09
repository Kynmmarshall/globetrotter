"""Profile, preferences, and favourites endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user, require_csrf
from app.models import User
from app.repositories import users as users_repo
from app.schemas.models import (
    FavouriteRequest,
    FavouriteResponse,
    Preferences,
    UpdatePreferencesRequest,
    UpdateProfileRequest,
    UserProfile,
)
from app.services import favourites_service, profile_service
from app.store import store

router = APIRouter(prefix="/api/v1/users", tags=["users"])


def _to_profile(user: User) -> UserProfile:
    favourite_count = len(users_repo.list_favourites(store.read(), user["id"]))
    return UserProfile(
        id=user["id"],
        email=user["email"],
        display_name=user["display_name"],
        bio=user["bio"],
        home_city=user["home_city"],
        avatar_url=user["avatar_url"],
        locale=user["locale"],
        preferences=Preferences.model_validate(user["preferences"] or {}),
        favourite_count=favourite_count,
        created_at=user["created_at"],
    )


@router.get("/me", response_model=UserProfile)
def read_me(current_user: User = Depends(get_current_user)) -> UserProfile:
    return _to_profile(current_user)


@router.patch("/me", response_model=UserProfile, dependencies=[Depends(require_csrf)])
def update_me(payload: UpdateProfileRequest, current_user: User = Depends(get_current_user)) -> UserProfile:
    user = profile_service.update_profile(current_user["id"], payload)
    return _to_profile(user)


@router.put("/me/preferences", response_model=UserProfile, dependencies=[Depends(require_csrf)])
def update_preferences(
    payload: UpdatePreferencesRequest, current_user: User = Depends(get_current_user)
) -> UserProfile:
    user = profile_service.update_preferences(current_user["id"], payload)
    return _to_profile(user)


@router.get("/me/favourites", response_model=list[FavouriteResponse])
def list_my_favourites(current_user: User = Depends(get_current_user)) -> list[FavouriteResponse]:
    favourites = favourites_service.list_favourites(current_user["id"])
    return [FavouriteResponse.model_validate(f) for f in favourites]


@router.post(
    "/me/favourites",
    response_model=FavouriteResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_csrf)],
)
def add_favourite(payload: FavouriteRequest, current_user: User = Depends(get_current_user)) -> FavouriteResponse:
    favourite = favourites_service.add_favourite(current_user["id"], payload.destination_id)
    return FavouriteResponse.model_validate(favourite)


@router.delete(
    "/me/favourites/{destination_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_csrf)],
)
def remove_favourite(destination_id: str, current_user: User = Depends(get_current_user)) -> None:
    favourites_service.remove_favourite(current_user["id"], destination_id)
