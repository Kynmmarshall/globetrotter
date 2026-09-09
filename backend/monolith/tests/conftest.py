from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

REAL_SEED_FILE = Path(__file__).resolve().parent.parent / "data" / "destinations.json"


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    """Isolate each test on its own JSON file, seeded from the real destination catalogue."""
    seed_copy = tmp_path / "destinations.json"
    shutil.copy(REAL_SEED_FILE, seed_copy)

    settings.data_file = tmp_path / "db.json"
    settings.seed_destinations_file = seed_copy

    return TestClient(app)


@pytest.fixture()
def seeded_destination_id() -> str:
    destinations = json.loads(REAL_SEED_FILE.read_text(encoding="utf-8"))
    return destinations[0]["id"]
