from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import csrf_headers, make_admin, register


def test_send_message_and_read_history(client: TestClient) -> None:
    register(client, email="chatty@example.com", display_name="Chatty")

    with client.websocket_connect("/ws/chat") as ws:
        ws.send_json({"type": "chat.send", "client_message_id": "msg-1", "text": "Hello, world!"})
        ack = ws.receive_json()
        assert ack["type"] == "chat.ack"
        assert ack["data"]["text"] == "Hello, world!"
        assert ack["data"]["sender_display_name"] == "Chatty"

    history = client.get("/api/v1/chat/messages")
    assert history.status_code == 200
    messages = history.json()["messages"]
    assert len(messages) == 1
    assert messages[0]["text"] == "Hello, world!"


def test_duplicate_client_message_id_is_idempotent(client: TestClient) -> None:
    register(client, email="retry@example.com")

    with client.websocket_connect("/ws/chat") as ws:
        for _ in range(2):
            ws.send_json({"type": "chat.send", "client_message_id": "same-id", "text": "Retry me"})
            ack = ws.receive_json()
            assert ack["type"] == "chat.ack"

    history = client.get("/api/v1/chat/messages")
    assert len(history.json()["messages"]) == 1


def test_empty_text_is_rejected_with_error(client: TestClient) -> None:
    register(client, email="empty@example.com")

    with client.websocket_connect("/ws/chat") as ws:
        ws.send_json({"type": "chat.send", "client_message_id": "empty-1", "text": ""})
        response = ws.receive_json()
        assert response["type"] == "error"


def test_history_pagination_next_before_sequence(client: TestClient) -> None:
    register(client, email="page@example.com")

    with client.websocket_connect("/ws/chat") as ws:
        for i in range(3):
            ws.send_json({"type": "chat.send", "client_message_id": f"page-{i}", "text": f"Message {i}"})
            ws.receive_json()

    first_page = client.get("/api/v1/chat/messages", params={"limit": 2}).json()
    assert len(first_page["messages"]) == 2
    assert first_page["next_before_sequence"] is not None

    second_page = client.get(
        "/api/v1/chat/messages", params={"limit": 2, "before_sequence": first_page["next_before_sequence"]}
    ).json()
    assert len(second_page["messages"]) == 1
    assert second_page["next_before_sequence"] is None


def test_report_message(client: TestClient) -> None:
    register(client, email="sender@example.com")
    with client.websocket_connect("/ws/chat") as ws:
        ws.send_json({"type": "chat.send", "client_message_id": "report-1", "text": "Report me"})
        ack = ws.receive_json()
    message_id = ack["data"]["id"]

    reporter = TestClient(client.app)
    reporter_session = register(reporter, email="reporter@example.com")
    response = reporter.post(
        f"/api/v1/chat/messages/{message_id}/report",
        json={"reason": "spam"},
        headers=csrf_headers(reporter_session),
    )
    assert response.status_code == 204


def test_hide_message_requires_admin_then_redacts_text(client: TestClient) -> None:
    session = register(client, email="mod-target@example.com")
    with client.websocket_connect("/ws/chat") as ws:
        ws.send_json({"type": "chat.send", "client_message_id": "hide-1", "text": "Should be hidden"})
        ack = ws.receive_json()
    message_id = ack["data"]["id"]

    forbidden_response = client.post(
        f"/api/v1/chat/messages/{message_id}/hide",
        json={"reason": "inappropriate"},
        headers=csrf_headers(session),
    )
    assert forbidden_response.status_code == 403

    make_admin(client, "mod-target@example.com")
    hide_response = client.post(
        f"/api/v1/chat/messages/{message_id}/hide",
        json={"reason": "inappropriate"},
        headers=csrf_headers(session),
    )
    assert hide_response.status_code == 200
    assert hide_response.json()["hidden"] is True

    history = client.get("/api/v1/chat/messages").json()
    assert history["messages"][0]["hidden"] is True
    assert history["messages"][0]["text"] != "Should be hidden"
