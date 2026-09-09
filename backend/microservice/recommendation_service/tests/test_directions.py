from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict:
        return self._payload


class _FakeAsyncClient:
    last_request_url: str | None = None

    def __init__(self, *args, **kwargs) -> None:
        pass

    async def __aenter__(self) -> "_FakeAsyncClient":
        return self

    async def __aexit__(self, *exc_info) -> None:
        return None

    async def get(self, url: str, params: dict | None = None):
        _FakeAsyncClient.last_request_url = url
        return _FakeResponse(
            200,
            {
                "code": "Ok",
                "routes": [
                    {
                        "distance": 1234.5,
                        "duration": 321.0,
                        "geometry": {"coordinates": [[11.50, 3.85], [11.52, 3.86]], "type": "LineString"},
                        "legs": [
                            {
                                "steps": [
                                    {
                                        "distance": 100.0,
                                        "duration": 30.0,
                                        "name": "Rue de la Paix",
                                        "maneuver": {"type": "depart"},
                                    },
                                    {
                                        "distance": 1134.5,
                                        "duration": 291.0,
                                        "name": "",
                                        "maneuver": {"type": "arrive"},
                                    },
                                ]
                            }
                        ],
                    }
                ],
            },
        )


class _FakeNoRouteAsyncClient(_FakeAsyncClient):
    async def get(self, url: str, params: dict | None = None):
        return _FakeResponse(200, {"code": "NoRoute", "routes": []})


@pytest.fixture()
def mock_osrm(monkeypatch):
    import app.services.directions_service as directions_module

    monkeypatch.setattr(directions_module.httpx, "AsyncClient", _FakeAsyncClient)
    return _FakeAsyncClient


def test_directions_between_two_coordinates(client: TestClient, mock_osrm) -> None:
    response = client.post(
        "/api/v1/directions",
        json={"start": {"lat": 3.848, "lng": 11.502}, "stops": [{"lat": 3.853, "lng": 11.508}]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["distance_meters"] == 1234.5
    assert len(body["steps"]) == 2
    assert body["steps"][0]["instruction"] == "Head out onto Rue de la Paix"
    assert body["steps"][-1]["instruction"] == "Arrive at your destination"


def test_directions_resolves_destination_id(client: TestClient, mock_osrm) -> None:
    response = client.post(
        "/api/v1/directions",
        json={"start": {"lat": 3.848, "lng": 11.502}, "stops": [{"destination_id": "dst-basilica"}]},
    )
    assert response.status_code == 200


def test_directions_unknown_destination_id_is_404(client: TestClient, mock_osrm) -> None:
    response = client.post(
        "/api/v1/directions",
        json={"start": {"lat": 3.848, "lng": 11.502}, "stops": [{"destination_id": "does-not-exist"}]},
    )
    assert response.status_code == 404


def test_directions_waypoint_needs_exactly_one_of_coords_or_id(client: TestClient, mock_osrm) -> None:
    response = client.post(
        "/api/v1/directions",
        json={"start": {"lat": 3.848, "lng": 11.502, "destination_id": "dst-basilica"}, "stops": [{"lat": 1, "lng": 1}]},
    )
    assert response.status_code == 422


def test_directions_no_route_found(client: TestClient, monkeypatch) -> None:
    import app.services.directions_service as directions_module

    monkeypatch.setattr(directions_module.httpx, "AsyncClient", _FakeNoRouteAsyncClient)
    response = client.post(
        "/api/v1/directions",
        json={"start": {"lat": 3.848, "lng": 11.502}, "stops": [{"lat": 3.853, "lng": 11.508}]},
    )
    assert response.status_code == 404
