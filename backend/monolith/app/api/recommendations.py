from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user_id
from app.schemas.models import RecommendedDestination
from app.services import recommendation_service
from app.services.auth_service import get_user_or_raise

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("", response_model=list[RecommendedDestination])
async def get_recommendations(
    limit: int = Query(default=10, ge=1, le=50),
    user_id: str = Depends(get_current_user_id),
) -> list[RecommendedDestination]:
    user = await get_user_or_raise(user_id)
    return await recommendation_service.recommend_for_user(user.get("interests", []), limit)
