"""Consistent error responses for the Itinerary Service API.

Deliberately duplicated (not imported) from the other services: each
microservice stays independently deployable with no shared code dependency.
"""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message


def not_found(message: str = "Resource not found") -> AppError:
    return AppError(status.HTTP_404_NOT_FOUND, "not_found", message)


def forbidden(message: str = "You do not have access to this resource") -> AppError:
    return AppError(status.HTTP_403_FORBIDDEN, "forbidden", message)


def unauthorized(message: str = "Please log in to continue.") -> AppError:
    return AppError(status.HTTP_401_UNAUTHORIZED, "unauthorized", message)


def bad_request(message: str) -> AppError:
    return AppError(status.HTTP_400_BAD_REQUEST, "bad_request", message)


def upstream_unavailable(message: str = "A dependent service is unavailable") -> AppError:
    return AppError(status.HTTP_502_BAD_GATEWAY, "upstream_unavailable", message)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "One or more fields are invalid.",
                    "details": jsonable_encoder(exc.errors()),
                }
            },
        )
