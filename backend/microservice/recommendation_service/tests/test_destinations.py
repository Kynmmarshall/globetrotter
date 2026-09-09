from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_destinations_returns_all_seeded(client: TestClient) -> None:
    response = client.get("/api/v1/destinations")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 13
    assert len(body["items"]) == 13


def test_filter_by_category(client: TestClient) -> None:
    response = client.get("/api/v1/destinations", params={"category": "heritage"})
    body = response.json()
    assert body["total"] == 4
    assert all(item["category"] == "heritage" for item in body["items"])


def test_search_by_text(client: TestClient) -> None:
    response = client.get("/api/v1/destinations", params={"q": "lac"})
    body = response.json()
    assert body["total"] >= 1
    assert any("lac" in item["name"].lower() for item in body["items"])


def test_get_destination_by_id(client: TestClient) -> None:
    response = client.get("/api/v1/destinations/dst-basilica")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "dst-basilica"
    assert body["image"]["primary"].startswith("/static/destinations/")
    assert len(body["image"]["variants"]) == 3


def test_get_missing_destination_is_404(client: TestClient) -> None:
    response = client.get("/api/v1/destinations/does-not-exist")
    assert response.status_code == 404


def test_pagination(client: TestClient) -> None:
    first_page = client.get("/api/v1/destinations", params={"limit": 5, "offset": 0}).json()
    second_page = client.get("/api/v1/destinations", params={"limit": 5, "offset": 5}).json()
    assert len(first_page["items"]) == 5
    assert len(second_page["items"]) == 5
    first_ids = {item["id"] for item in first_page["items"]}
    second_ids = {item["id"] for item in second_page["items"]}
    assert first_ids.isdisjoint(second_ids)
