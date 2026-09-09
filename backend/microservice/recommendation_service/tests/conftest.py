from __future__ import annotations

from pathlib import Path

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.services import destination_service

REPO_ROOT = Path(__file__).resolve().parents[4]
PRIVATE_KEY = (REPO_ROOT / "infra" / "keys" / "jwt_private_key.pem").read_text(encoding="utf-8")


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    """Temp JSON file per test, pre-seeded with the real 13-destination catalogue."""
    original_data_file = settings.data_file
    settings.data_file = tmp_path / "test-db.json"
    destination_service.seed_from_json()

    test_client = TestClient(app)
    yield test_client

    settings.data_file = original_data_file


def make_token(user_id: str) -> str:
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(minutes=15),
        "iss": settings.jwt_issuer,
        "tv": 0,
    }
    return jwt.encode(payload, PRIVATE_KEY, algorithm=settings.jwt_algorithm)


def auth_headers(user_id: str) -> dict:
    return {"Authorization": f"Bearer {make_token(user_id)}"}
