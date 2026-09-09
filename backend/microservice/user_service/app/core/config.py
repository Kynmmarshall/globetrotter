"""Application configuration for the User Service (auth, profile, chat)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# app/core/config.py -> core -> app -> user_service (this service's own root,
# containing pyproject.toml) -> microservice -> backend -> repo root.
# Verified explicitly (see backend BASE_DIR bug lesson in
# /memories/repo/globetrotter.md) rather than assumed. Chained .parent calls
# (not .parents[N] indexing) so this degrades to "/" instead of raising
# IndexError when running in Docker, where the directory tree above /srv/app
# is much shallower than on the host -- REPO_ROOT is only a fallback default
# for the JWT key paths below, which are always overridden by env vars there.
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

    jwt_private_key_path: Path = REPO_ROOT / "infra" / "keys" / "jwt_private_key.pem"
    jwt_public_key_path: Path = REPO_ROOT / "infra" / "keys" / "jwt_public_key.pem"
    jwt_algorithm: str = "RS256"
    jwt_issuer: str = "globetrotter-user-service"
    jwt_access_token_minutes: int = 15
    jwt_refresh_token_days: int = 30

    cookie_secure: bool = False
    cookie_domain: str | None = None
    access_cookie_name: str = "gt_access"
    refresh_cookie_name: str = "gt_refresh"
    csrf_cookie_name: str = "gt_csrf"
    csrf_header_name: str = "X-CSRF-Token"

    cors_origins: list[str] = ["http://localhost:5173"]

    chat_max_message_length: int = 1000
    chat_history_page_size: int = 50

    @property
    def rabbitmq_url(self) -> str:
        return f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}@{self.rabbitmq_host}:{self.rabbitmq_port}/"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
