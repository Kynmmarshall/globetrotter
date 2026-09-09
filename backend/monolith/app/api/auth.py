from __future__ import annotations

from fastapi import APIRouter

from app.schemas.models import LoginRequest, RegisterRequest, TokenResponse
from app.services import auth_service

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(payload: RegisterRequest) -> TokenResponse:
    return await auth_service.register(payload)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest) -> TokenResponse:
    return await auth_service.login(payload)
