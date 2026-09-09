from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import csrf_headers, register


def test_register_returns_tokens_and_sets_cookies(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "new@example.com", "password": "correct-horse-1", "display_name": "New User"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["access_token"]
    assert body["csrf_token"]
    assert "gt_access" in response.cookies
    assert "gt_refresh" in response.cookies
    assert "gt_csrf" in response.cookies


def test_register_duplicate_email_conflicts(client: TestClient) -> None:
    register(client, email="dup@example.com")
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "password": "another-pass-1", "display_name": "Someone Else"},
    )
    assert response.status_code == 409


def test_login_wrong_password_is_unauthorized(client: TestClient) -> None:
    register(client, email="login@example.com", password="correct-horse-1")
    response = client.post(
        "/api/v1/auth/login", json={"email": "login@example.com", "password": "wrong-password"}
    )
    assert response.status_code == 401


def test_login_success(client: TestClient) -> None:
    register(client, email="login2@example.com", password="correct-horse-1")
    response = client.post(
        "/api/v1/auth/login", json={"email": "login2@example.com", "password": "correct-horse-1"}
    )
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_me_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401


def test_me_returns_profile_after_register(client: TestClient) -> None:
    register(client, email="profile@example.com", display_name="Profile Person")
    response = client.get("/api/v1/users/me")
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "profile@example.com"
    assert body["display_name"] == "Profile Person"
    assert body["favourite_count"] == 0


def test_logout_requires_csrf_header(client: TestClient) -> None:
    register(client, email="logout@example.com")
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 403


def test_logout_then_refresh_fails(client: TestClient) -> None:
    session = register(client, email="logout2@example.com")
    logout_response = client.post("/api/v1/auth/logout", headers=csrf_headers(session))
    assert logout_response.status_code == 204

    refresh_response = client.post("/api/v1/auth/refresh")
    assert refresh_response.status_code == 401


def test_refresh_rotates_tokens(client: TestClient) -> None:
    register(client, email="refresh@example.com")
    first_refresh_cookie = client.cookies.get("gt_refresh")

    response = client.post("/api/v1/auth/refresh")
    assert response.status_code == 200
    assert client.cookies.get("gt_refresh") != first_refresh_cookie

    # The rotated-out refresh token must no longer work.
    client.cookies.set("gt_refresh", first_refresh_cookie)
    reuse_response = client.post("/api/v1/auth/refresh")
    assert reuse_response.status_code == 401
