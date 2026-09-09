"""Application configuration for the Phase 1 monolith.

Deliberately minimal: one process, one JSON file, one shared secret. This is
the assignment baseline, not a production security posture.
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# app/core/config.py -> app/core -> app -> backend/monolith (the project root
# containing data/, static/, pyproject.toml), NOT the "app" package directory.
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MONOLITH_", env_file=".env", extra="ignore")

    data_file: Path = BASE_DIR / "data" / "db.json"
    seed_destinations_file: Path = BASE_DIR / "data" / "destinations.json"
    static_dir: Path = BASE_DIR / "static"

    jwt_secret: str = "dev-only-monolith-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60

    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
