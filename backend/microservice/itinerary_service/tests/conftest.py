from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.errors import bad_request
from app.main import app

REPO_ROOT = Path(__file__).resolve().parents[4]
PRIVATE_KEY = (REPO_ROOT / "infra" / "keys" / "jwt_private_key.pem").read_text(encoding="utf-8")

KNOWN_DESTINATIONS = {
    "dst-basilica": {
        "destination_id": "dst-basilica",
        "name": "Basilica",
        "category": "heritage",
        "lat": 3.8531,
        "lng": 11.5083,
        "image": {"alt": "Basilica", "primary": "/static/destinations/basilica-960.webp", "variants": []},
    },
    "dst-lac-municipal": {
        "destination_id": "dst-lac-municipal",
        "name": "Lac Municipal",
        "category": "nature",
        "lat": 3.86,
        "lng": 11.52,
        "image": {"alt": "Lac Municipal", "primary": "/static/destinations/lac_municipal-960.webp", "variants": []},
    },
}


@pytest.fixture()
def client(tmp_path: Path, monkeypatch) -> TestClient:
    original_data_file = settings.data_file
    settings.data_file = tmp_path / "test-db.json"

    async def fake_fetch_destination_snapshot(destination_id: str) -> dict:
        if destination_id not in KNOWN_DESTINATIONS:
            raise bad_request(f"No destination with id {destination_id!r}.")
        return KNOWN_DESTINATIONS[destination_id]

    monkeypatch.setattr(
        "app.services.itinerary_service.fetch_destination_snapshot", fake_fetch_destination_snapshot
    )

    test_client = TestClient(app)
    yield test_client

    settings.data_file = original_data_file


def make_token(user_id: str) -> str:
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
