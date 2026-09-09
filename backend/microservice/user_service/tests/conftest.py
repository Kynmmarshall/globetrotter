from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    """Each test gets its own temp JSON file.

    Deliberately NOT using `with TestClient(app) as c`: entering the context
    manager would run the app's lifespan, which tries to connect to RabbitMQ
    and start the outbox/chat background tasks. Tests exercise the HTTP/WS API
    directly and should not depend on Docker/RabbitMQ being available.
    """
    original_data_file = settings.data_file
    settings.data_file = tmp_path / "test-db.json"

    test_client = TestClient(app)
    yield test_client

    settings.data_file = original_data_file


def register(client: TestClient, *, email: str = "amara@example.com", password: str = "correct-horse-1", display_name: str = "Amara") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": display_name},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    return {"access_token": body["access_token"], "csrf_token": body["csrf_token"]}


def csrf_headers(session: dict) -> dict:
    return {"X-CSRF-Token": session["csrf_token"]}


def make_admin(client: TestClient, email: str) -> None:
    from app.store import store

    def mutator(db: dict) -> None:
        user = next(u for u in db["users"] if u["email"] == email.lower())
        user["is_admin"] = True

    store.mutate(mutator)
