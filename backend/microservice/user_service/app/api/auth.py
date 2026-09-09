"""Authentication endpoints: register, login, refresh, logout."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, status

from app.api.deps import require_csrf
from app.core.config import settings
from app.core.errors import unauthorized
from app.schemas.models import LoginRequest, RegisterRequest, TokenResponse
from app.services import auth_service
from app.services.auth_service import IssuedSession

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _set_session_cookies(response: Response, session: IssuedSession) -> None:
    response.set_cookie(
        settings.access_cookie_name,
        session.access_token,
        max_age=settings.jwt_access_token_minutes * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        domain=settings.cookie_domain,
        path="/",
    )
    response.set_cookie(
        settings.refresh_cookie_name,
        session.refresh_token,
        max_age=settings.jwt_refresh_token_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        domain=settings.cookie_domain,
        path="/api/v1/auth",
    )
    response.set_cookie(
        settings.csrf_cookie_name,
        session.csrf_token,
        max_age=settings.jwt_refresh_token_days * 24 * 60 * 60,
        httponly=False,
        secure=settings.cookie_secure,
        samesite="lax",
        domain=settings.cookie_domain,
        path="/",
    )


def _clear_session_cookies(response: Response) -> None:
    for name, path in (
        (settings.access_cookie_name, "/"),
        (settings.refresh_cookie_name, "/api/v1/auth"),
        (settings.csrf_cookie_name, "/"),
    ):
        response.delete_cookie(name, path=path, domain=settings.cookie_domain)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, request: Request, response: Response) -> TokenResponse:
    session = auth_service.register(
        email=payload.email,
        password=payload.password,
        display_name=payload.display_name,
        user_agent=request.headers.get("user-agent"),
    )
    _set_session_cookies(response, session)
    return TokenResponse(access_token=session.access_token, csrf_token=session.csrf_token)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, response: Response) -> TokenResponse:
    session = auth_service.login(
        email=payload.email, password=payload.password, user_agent=request.headers.get("user-agent")
    )
    _set_session_cookies(response, session)
    return TokenResponse(access_token=session.access_token, csrf_token=session.csrf_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: Request, response: Response) -> TokenResponse:
    refresh_token = request.cookies.get(settings.refresh_cookie_name, "")
    if not refresh_token:
        raise unauthorized("No active session to refresh.")

    session = auth_service.refresh(refresh_token=refresh_token, user_agent=request.headers.get("user-agent"))
    _set_session_cookies(response, session)
    return TokenResponse(access_token=session.access_token, csrf_token=session.csrf_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_csrf)])
def logout(request: Request, response: Response) -> None:
    refresh_token = request.cookies.get(settings.refresh_cookie_name, "")
    if refresh_token:
        auth_service.logout(refresh_token=refresh_token)
    _clear_session_cookies(response)
