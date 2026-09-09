from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import auth_headers


def _create_trip_with_item(client: TestClient) -> str:
    headers = auth_headers("user-1")
    trip_id = client.post(
        "/api/v1/itineraries",
        json={"title": "Yaounde Weekend", "start_date": "2026-10-01", "end_date": "2026-10-03"},
        headers=headers,
    ).json()["id"]
    client.post(f"/api/v1/itineraries/{trip_id}/items", json={"destination_id": "dst-basilica", "day": 1}, headers=headers)
    return trip_id


def test_create_share_link_and_read_publicly(client: TestClient) -> None:
    trip_id = _create_trip_with_item(client)
    headers = auth_headers("user-1")

    share_response = client.post(f"/api/v1/itineraries/{trip_id}/share", headers=headers)
    assert share_response.status_code == 200
    token = share_response.json()["token"]

    public_response = client.get(f"/api/v1/public/itineraries/{token}")
    assert public_response.status_code == 200
    body = public_response.json()
    assert body["title"] == "Yaounde Weekend"
    assert len(body["items"]) == 1
    assert "notes" not in body["items"][0]


def test_revoked_share_link_is_no_longer_readable(client: TestClient) -> None:
    trip_id = _create_trip_with_item(client)
    headers = auth_headers("user-1")

    token = client.post(f"/api/v1/itineraries/{trip_id}/share", headers=headers).json()["token"]
    revoke_response = client.delete(f"/api/v1/itineraries/{trip_id}/share", headers=headers)
    assert revoke_response.status_code == 204

    public_response = client.get(f"/api/v1/public/itineraries/{token}")
    assert public_response.status_code == 404


def test_creating_share_link_twice_replaces_old_token(client: TestClient) -> None:
    trip_id = _create_trip_with_item(client)
    headers = auth_headers("user-1")

    first_token = client.post(f"/api/v1/itineraries/{trip_id}/share", headers=headers).json()["token"]
    second_token = client.post(f"/api/v1/itineraries/{trip_id}/share", headers=headers).json()["token"]
    assert first_token != second_token

    assert client.get(f"/api/v1/public/itineraries/{first_token}").status_code == 404
    assert client.get(f"/api/v1/public/itineraries/{second_token}").status_code == 200


def test_invalid_share_token_is_404(client: TestClient) -> None:
    response = client.get("/api/v1/public/itineraries/not-a-real-token")
    assert response.status_code == 404
