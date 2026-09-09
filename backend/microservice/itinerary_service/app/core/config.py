"""Application configuration for the Itinerary Service."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# app/core/config.py -> core -> app -> itinerary_service (this service's own
# root) -> microservice -> backend -> repo root. Chained .parent calls (not
# .parents[N] indexing) so this degrades to "/" instead of raising IndexError
# in Docker, where the tree above /srv/app is much shallower than on the
# host -- REPO_ROOT is only a fallback default for the JWT public key path
# below, always overridden by an env var there.
SERVICE_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = SERVICE_DIR.parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", env_file=".env", extra="ignore")

    environment: str = "development"
    log_level: str = "INFO"

    data_file: Path = SERVICE_DIR / "data" / "db.json"

    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "globetrotter"
    rabbitmq_password: str = "change-me-in-local-env"

    jwt_public_key_path: Path = REPO_ROOT / "infra" / "keys" / "jwt_public_key.pem"
    jwt_algorithm: str = "RS256"
    jwt_issuer: str = "globetrotter-user-service"

    cors_origins: list[str] = ["http://localhost:5173"]

    recommendation_service_base_url: str = "http://localhost:8002"
    recommendation_service_timeout_seconds: float = 3.0

    max_items_per_itinerary: int = 60

    @property
    def rabbitmq_url(self) -> str:
        return f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}@{self.rabbitmq_host}:{self.rabbitmq_port}/"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
