from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import csrf_headers, register


def test_update_profile_fields(client: TestClient) -> None:
    session = register(client, email="edit@example.com")
    response = client.patch(
        "/api/v1/users/me",
        json={"display_name": "New Name", "bio": "I love maps.", "home_city": "Yaounde"},
        headers=csrf_headers(session),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["display_name"] == "New Name"
    assert body["bio"] == "I love maps."
    assert body["home_city"] == "Yaounde"


def test_update_profile_requires_csrf(client: TestClient) -> None:
    register(client, email="edit2@example.com")
    response = client.patch("/api/v1/users/me", json={"display_name": "No CSRF"})
    assert response.status_code == 403


def test_update_preferences(client: TestClient) -> None:
    session = register(client, email="prefs@example.com")
    response = client.put(
        "/api/v1/users/me/preferences",
        json={"interests": ["nature", "history"], "budget_band": "medium", "pace": "balanced"},
        headers=csrf_headers(session),
    )
    assert response.status_code == 200
    prefs = response.json()["preferences"]
    assert prefs["interests"] == ["nature", "history"]
    assert prefs["budget_band"] == "medium"
