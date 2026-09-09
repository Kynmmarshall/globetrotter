from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import auth_headers


def _create_trip(client: TestClient, user: str = "user-1") -> dict:
    response = client.post(
        "/api/v1/itineraries",
        json={"title": "Yaounde Weekend", "start_date": "2026-10-01", "end_date": "2026-10-03"},
        headers=auth_headers(user),
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/itineraries")
    assert response.status_code == 401


def test_create_and_get_itinerary(client: TestClient) -> None:
    created = _create_trip(client)
    assert created["title"] == "Yaounde Weekend"
    assert created["items"] == []

    response = client.get(f"/api/v1/itineraries/{created['id']}", headers=auth_headers("user-1"))
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_end_date_before_start_date_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/v1/itineraries",
        json={"title": "Bad Trip", "start_date": "2026-10-03", "end_date": "2026-10-01"},
        headers=auth_headers("user-1"),
    )
    assert response.status_code == 422


def test_list_only_returns_own_trips(client: TestClient) -> None:
    _create_trip(client, user="user-1")
    _create_trip(client, user="user-2")

    response = client.get("/api/v1/itineraries", headers=auth_headers("user-1"))
    body = response.json()
    assert len(body) == 1


def test_other_user_cannot_read_private_trip(client: TestClient) -> None:
    created = _create_trip(client, user="user-1")
    response = client.get(f"/api/v1/itineraries/{created['id']}", headers=auth_headers("user-2"))
    assert response.status_code == 403


def test_update_itinerary_fields(client: TestClient) -> None:
    created = _create_trip(client)
    response = client.patch(
        f"/api/v1/itineraries/{created['id']}", json={"title": "Renamed Trip"}, headers=auth_headers("user-1")
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Renamed Trip"
    assert response.json()["revision"] == 2


def test_delete_itinerary(client: TestClient) -> None:
    created = _create_trip(client)
    response = client.delete(f"/api/v1/itineraries/{created['id']}", headers=auth_headers("user-1"))
    assert response.status_code == 204

    get_response = client.get(f"/api/v1/itineraries/{created['id']}", headers=auth_headers("user-1"))
    assert get_response.status_code == 404
