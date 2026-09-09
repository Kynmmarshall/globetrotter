"""Personalized (or anonymous-friendly) destination recommendations."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user_id_optional
from app.schemas.models import DestinationResponse, RecommendationItem, RecommendationListResponse
from app.services import recommendation_service

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


@router.get("", response_model=RecommendationListResponse)
def get_recommendations(
    limit: int = Query(default=10, ge=1, le=50),
    user_id: str | None = Depends(get_current_user_id_optional),
) -> RecommendationListResponse:
    ranked, personalized = recommendation_service.get_recommendations(user_id=user_id, limit=limit)
    items = [
        RecommendationItem(destination=DestinationResponse.model_validate(r.destination), reason=r.reason)
        for r in ranked
    ]
    return RecommendationListResponse(items=items, personalized=personalized)
