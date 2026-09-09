from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.core.config import settings
from tests.test_auth import register


def test_create_and_list_itinerary_round_trips(client: TestClient, seeded_destination_id: str) -> None:
    token = register(client, email="planner@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/itineraries",
        headers=headers,
        json={
            "title": "Yaounde Weekend",
            "start_date": "2026-10-01",
            "end_date": "2026-10-03",
            "items": [{"destination_id": seeded_destination_id, "day": 1, "position": 0}],
        },
    )
    assert create_response.status_code == 201, create_response.text
    created = create_response.json()
    assert created["items"][0]["destination"]["id"] == seeded_destination_id

    list_response = client.get("/itineraries", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


def test_create_itinerary_rejects_unknown_destination(client: TestClient) -> None:
    token = register(client, email="planner2@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/itineraries",
        headers=headers,
        json={
            "title": "Bad Trip",
            "start_date": "2026-10-01",
            "end_date": "2026-10-03",
            "items": [{"destination_id": "does-not-exist", "day": 1, "position": 0}],
        },
    )
    assert response.status_code == 404


def test_another_user_cannot_read_a_private_itinerary(client: TestClient, seeded_destination_id: str) -> None:
    owner_token = register(client, email="owner@example.com")
    other_token = register(client, email="intruder@example.com")

    create_response = client.post(
        "/itineraries",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "title": "Private Trip",
            "start_date": "2026-10-01",
            "end_date": "2026-10-02",
            "items": [{"destination_id": seeded_destination_id, "day": 1, "position": 0}],
        },
    )
    itinerary_id = create_response.json()["id"]

    response = client.get(
        f"/itineraries/{itinerary_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert response.status_code == 403


def test_itinerary_persists_to_disk(client: TestClient, seeded_destination_id: str) -> None:
    token = register(client, email="persist@example.com")
    client.post(
        "/itineraries",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Persisted Trip",
            "start_date": "2026-11-01",
            "end_date": "2026-11-02",
            "items": [{"destination_id": seeded_destination_id, "day": 1, "position": 0}],
        },
    )

    on_disk = json.loads(settings.data_file.read_text(encoding="utf-8"))
    assert any(itinerary["title"] == "Persisted Trip" for itinerary in on_disk["itineraries"])
