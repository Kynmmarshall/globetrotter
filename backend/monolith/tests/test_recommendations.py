from __future__ import annotations

from fastapi.testclient import TestClient

from tests.test_auth import register


def test_recommendations_require_auth(client: TestClient) -> None:
    response = client.get("/recommendations")
    assert response.status_code == 401


def test_recommendations_return_results_for_new_user(client: TestClient) -> None:
    token = register(client, email="rec@example.com")
    response = client.get("/recommendations", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) > 0
    assert all("reason" in item for item in body)
