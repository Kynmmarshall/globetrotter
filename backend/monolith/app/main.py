from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import auth, destinations, itineraries, recommendations, users
from app.core.config import settings
from app.core.errors import register_error_handlers

app = FastAPI(
    title="GlobeTrotter Monolith (Phase 1)",
    description=(
        "Single-process FastAPI application backed by a JSON file. "
        "Demonstrates the assignment's Phase 1 baseline and its limitations "
        "(no transactions, no horizontal scaling, single point of failure)."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)

# Destination images live in this backend's own static/ folder (see
# scripts/build_destination_assets.py) and are served directly, not proxied
# through the frontend build.
settings.static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(destinations.router)
app.include_router(recommendations.router)
app.include_router(itineraries.router)


@app.get("/health", tags=["ops"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
