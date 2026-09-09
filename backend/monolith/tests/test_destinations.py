from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_destinations_returns_seeded_catalogue(client: TestClient) -> None:
    response = client.get("/destinations")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 13
    assert all("image" in item for item in body)


def test_list_destinations_filters_by_category(client: TestClient) -> None:
    response = client.get("/destinations", params={"category": "heritage"})
    assert response.status_code == 200
    body = response.json()
    assert body
    assert all(item["category"] == "heritage" for item in body)


def test_list_destinations_filters_by_search_text(client: TestClient) -> None:
    response = client.get("/destinations", params={"search": "reunification"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["slug"] == "reunification_monument"


def test_get_destination_by_id(client: TestClient, seeded_destination_id: str) -> None:
    response = client.get(f"/destinations/{seeded_destination_id}")
    assert response.status_code == 200
    assert response.json()["id"] == seeded_destination_id


def test_get_destination_404_for_unknown_id(client: TestClient) -> None:
    response = client.get("/destinations/does-not-exist")
    assert response.status_code == 404
