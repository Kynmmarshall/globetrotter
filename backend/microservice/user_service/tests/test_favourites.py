from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import csrf_headers, register


def test_add_list_remove_favourite(client: TestClient) -> None:
    session = register(client, email="fav@example.com")

    add_response = client.post(
        "/api/v1/users/me/favourites", json={"destination_id": "dst-basilica"}, headers=csrf_headers(session)
    )
    assert add_response.status_code == 201
    assert add_response.json()["destination_id"] == "dst-basilica"

    list_response = client.get("/api/v1/users/me/favourites")
    assert list_response.status_code == 200
    assert [f["destination_id"] for f in list_response.json()] == ["dst-basilica"]

    profile_response = client.get("/api/v1/users/me")
    assert profile_response.json()["favourite_count"] == 1

    remove_response = client.delete("/api/v1/users/me/favourites/dst-basilica", headers=csrf_headers(session))
    assert remove_response.status_code == 204

    list_after_remove = client.get("/api/v1/users/me/favourites")
    assert list_after_remove.json() == []


def test_adding_same_favourite_twice_is_idempotent(client: TestClient) -> None:
    session = register(client, email="fav2@example.com")
    for _ in range(2):
        response = client.post(
            "/api/v1/users/me/favourites", json={"destination_id": "dst-lac"}, headers=csrf_headers(session)
        )
        assert response.status_code == 201

    list_response = client.get("/api/v1/users/me/favourites")
    assert len(list_response.json()) == 1


def test_removing_missing_favourite_is_not_found(client: TestClient) -> None:
    session = register(client, email="fav3@example.com")
    response = client.delete("/api/v1/users/me/favourites/does-not-exist", headers=csrf_headers(session))
    assert response.status_code == 404
