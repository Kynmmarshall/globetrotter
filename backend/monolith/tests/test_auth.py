from __future__ import annotations

from fastapi.testclient import TestClient


def register(client: TestClient, email: str = "user@example.com") -> str:
    response = client.post(
        "/register",
        json={"email": email, "password": "correct-horse-1", "display_name": "Ada"},
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def test_register_returns_access_token(client: TestClient) -> None:
    token = register(client)
    assert token


def test_register_rejects_duplicate_email(client: TestClient) -> None:
    register(client, email="dup@example.com")
    response = client.post(
        "/register",
        json={"email": "dup@example.com", "password": "another-password-1", "display_name": "Bob"},
    )
    assert response.status_code == 409


def test_login_succeeds_with_correct_credentials(client: TestClient) -> None:
    register(client, email="login@example.com")
    response = client.post("/login", json={"email": "login@example.com", "password": "correct-horse-1"})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_rejects_wrong_password(client: TestClient) -> None:
    register(client, email="wrong@example.com")
    response = client.post("/login", json={"email": "wrong@example.com", "password": "not-the-password"})
    assert response.status_code == 401


def test_me_requires_bearer_token(client: TestClient) -> None:
    response = client.get("/users/me")
    assert response.status_code == 401


def test_me_returns_current_user(client: TestClient) -> None:
    token = register(client, email="me@example.com")
    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"
