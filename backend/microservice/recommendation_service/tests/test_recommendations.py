from __future__ import annotations

from fastapi.testclient import TestClient

from app.repositories import preferences as preferences_repo
from app.store import store
from tests.conftest import auth_headers


def test_anonymous_recommendations_are_not_personalized(client: TestClient) -> None:
    response = client.get("/api/v1/recommendations")
    assert response.status_code == 200
    body = response.json()
    assert body["personalized"] is False
    assert len(body["items"]) > 0
    assert all(item["reason"] == "Popular in Yaounde" for item in body["items"])


def test_authenticated_user_without_preferences_gets_fallback(client: TestClient) -> None:
    response = client.get("/api/v1/recommendations", headers=auth_headers("user-without-prefs"))
    assert response.status_code == 200
    assert response.json()["personalized"] is False


def test_personalized_recommendations_match_interests(client: TestClient) -> None:
    store.mutate(
        lambda db: preferences_repo.upsert_preferences(db, user_id="user-nature-fan", preferences={"interests": ["nature"]})
    )

    response = client.get("/api/v1/recommendations", headers=auth_headers("user-nature-fan"))
    assert response.status_code == 200
    body = response.json()
    assert body["personalized"] is True
    assert len(body["items"]) > 0
    for item in body["items"]:
        assert "nature" in item["reason"].lower()
        assert item["destination"]["category"] == "nature" or "nature" in [
            t.lower() for t in item["destination"]["tags"]
        ]


def test_personalized_recommendations_exclude_favourites(client: TestClient) -> None:
    def mutator(db):
        preferences_repo.upsert_preferences(db, user_id="user-with-fav", preferences={"interests": ["nature"]})
        preferences_repo.apply_favourite_change(
            db, user_id="user-with-fav", destination_id="dst-lac-municipal", action="added"
        )

    store.mutate(mutator)

    response = client.get("/api/v1/recommendations", headers=auth_headers("user-with-fav"))
    body = response.json()
    destination_ids = [item["destination"]["id"] for item in body["items"]]
    assert "dst-lac-municipal" not in destination_ids
