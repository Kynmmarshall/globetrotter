from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_id
from app.schemas.models import UserPublic
from app.services.auth_service import get_public_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserPublic)
async def get_me(user_id: str = Depends(get_current_user_id)) -> UserPublic:
    return await get_public_user(user_id)
