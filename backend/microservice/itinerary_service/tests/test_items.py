from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import auth_headers


def _create_trip(client: TestClient) -> str:
    response = client.post(
        "/api/v1/itineraries",
        json={"title": "Yaounde Weekend", "start_date": "2026-10-01", "end_date": "2026-10-03"},
        headers=auth_headers("user-1"),
    )
    return response.json()["id"]


def test_add_item_validates_and_stores_snapshot(client: TestClient) -> None:
    trip_id = _create_trip(client)
    response = client.post(
        f"/api/v1/itineraries/{trip_id}/items",
        json={"destination_id": "dst-basilica", "day": 1, "notes": "Morning visit"},
        headers=auth_headers("user-1"),
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["destination_id"] == "dst-basilica"
    assert body["day"] == 1
    assert body["position"] == 1
    assert body["destination_snapshot"]["name"] == "Basilica"


def test_add_item_unknown_destination_is_rejected(client: TestClient) -> None:
    trip_id = _create_trip(client)
    response = client.post(
        f"/api/v1/itineraries/{trip_id}/items",
        json={"destination_id": "does-not-exist", "day": 1},
        headers=auth_headers("user-1"),
    )
    assert response.status_code == 400


def test_items_in_same_day_get_increasing_positions(client: TestClient) -> None:
    trip_id = _create_trip(client)
    headers = auth_headers("user-1")
    first = client.post(
        f"/api/v1/itineraries/{trip_id}/items", json={"destination_id": "dst-basilica", "day": 1}, headers=headers
    ).json()
    second = client.post(
        f"/api/v1/itineraries/{trip_id}/items",
        json={"destination_id": "dst-lac-municipal", "day": 1},
        headers=headers,
    ).json()
    assert first["position"] == 1
    assert second["position"] == 2


def test_move_item_up_swaps_positions(client: TestClient) -> None:
    trip_id = _create_trip(client)
    headers = auth_headers("user-1")
    first = client.post(
        f"/api/v1/itineraries/{trip_id}/items", json={"destination_id": "dst-basilica", "day": 1}, headers=headers
    ).json()
    second = client.post(
        f"/api/v1/itineraries/{trip_id}/items",
        json={"destination_id": "dst-lac-municipal", "day": 1},
        headers=headers,
    ).json()

    move_response = client.post(
        f"/api/v1/itineraries/{trip_id}/items/{second['id']}/move", json={"direction": "up"}, headers=headers
    )
    assert move_response.status_code == 200
    items = move_response.json()["items"]
    items_by_id = {item["id"]: item for item in items}
    assert items_by_id[second["id"]]["position"] == 1
    assert items_by_id[first["id"]]["position"] == 2


def test_move_item_at_edge_is_a_no_op(client: TestClient) -> None:
    trip_id = _create_trip(client)
    headers = auth_headers("user-1")
    item = client.post(
        f"/api/v1/itineraries/{trip_id}/items", json={"destination_id": "dst-basilica", "day": 1}, headers=headers
    ).json()

    response = client.post(
        f"/api/v1/itineraries/{trip_id}/items/{item['id']}/move", json={"direction": "up"}, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["items"][0]["position"] == 1


def test_update_item_notes_and_cost(client: TestClient) -> None:
    trip_id = _create_trip(client)
    headers = auth_headers("user-1")
    item = client.post(
        f"/api/v1/itineraries/{trip_id}/items", json={"destination_id": "dst-basilica", "day": 1}, headers=headers
    ).json()

    response = client.patch(
        f"/api/v1/itineraries/{trip_id}/items/{item['id']}",
        json={"notes": "Bring a hat", "estimated_cost": 15.5},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["notes"] == "Bring a hat"
    assert response.json()["estimated_cost"] == 15.5


def test_delete_item(client: TestClient) -> None:
    trip_id = _create_trip(client)
    headers = auth_headers("user-1")
    item = client.post(
        f"/api/v1/itineraries/{trip_id}/items", json={"destination_id": "dst-basilica", "day": 1}, headers=headers
    ).json()

    response = client.delete(f"/api/v1/itineraries/{trip_id}/items/{item['id']}", headers=headers)
    assert response.status_code == 204

    trip = client.get(f"/api/v1/itineraries/{trip_id}", headers=headers).json()
    assert trip["items"] == []


def test_other_user_cannot_add_item_to_someone_elses_trip(client: TestClient) -> None:
    trip_id = _create_trip(client)
    response = client.post(
        f"/api/v1/itineraries/{trip_id}/items",
        json={"destination_id": "dst-basilica", "day": 1},
        headers=auth_headers("user-2"),
    )
    assert response.status_code == 403
