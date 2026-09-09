"""Driving directions via an OSRM-compatible routing provider.

Uses the public OSRM demo server by default (settings.osrm_base_url) -- see
PROJECT_PLAN.md section 11 for the documented self-hosting path for a
production deployment. All outbound requests go through the backend with an
explicit timeout; the browser never calls the routing provider directly.
"""

from __future__ import annotations

import httpx

from app.core.config import settings
from app.core.errors import bad_request, not_found, upstream_unavailable
from app.repositories import destinations as destinations_repo
from app.schemas.models import DirectionsRequest, DirectionsResponse, RouteStep, Waypoint
from app.store import store

_MANEUVER_VERBS = {
    "depart": "Head out",
    "turn": "Turn",
    "continue": "Continue",
    "merge": "Merge",
    "on ramp": "Take the ramp",
    "off ramp": "Take the exit",
    "fork": "Keep",
    "end of road": "At the end of the road, turn",
    "roundabout": "Enter the roundabout and take an exit",
    "rotary": "Enter the roundabout and take an exit",
    "roundabout turn": "At the roundabout, turn",
    "notification": "Continue",
    "arrive": "Arrive at your destination",
    "new name": "Continue",
}


def _describe_step(maneuver: dict, road_name: str) -> str:
    maneuver_type = maneuver.get("type", "")
    modifier = maneuver.get("modifier")
    verb = _MANEUVER_VERBS.get(maneuver_type, "Continue")

    if maneuver_type == "arrive":
        return verb

    parts = [verb]
    if modifier and maneuver_type in {"turn", "end of road", "roundabout turn", "fork", "off ramp"}:
        parts.append(modifier)
    if road_name:
        parts.append(f"onto {road_name}")
    return " ".join(parts)


def _resolve_coordinates(waypoint: Waypoint) -> tuple[float, float]:
    if waypoint.destination_id is not None:
        destination = destinations_repo.get_by_id(store.read(), waypoint.destination_id)
        if destination is None:
            raise not_found(f"No destination with id {waypoint.destination_id!r}.")
        return destination["lat"], destination["lng"]
    return waypoint.lat, waypoint.lng  # both guaranteed non-None by the schema validator


async def get_directions(req: DirectionsRequest) -> DirectionsResponse:
    waypoints = [req.start, *req.stops]
    if len(waypoints) > settings.directions_max_stops + 1:
        raise bad_request(
            f"Too many stops: {len(waypoints) - 1} requested, provider limit is {settings.directions_max_stops}."
        )

    coordinates = [_resolve_coordinates(wp) for wp in waypoints]
    coordinate_str = ";".join(f"{lng},{lat}" for lat, lng in coordinates)
    url = f"{settings.osrm_base_url}/route/v1/{req.profile}/{coordinate_str}"

    try:
        async with httpx.AsyncClient(timeout=settings.osrm_timeout_seconds) as client:
            response = await client.get(url, params={"overview": "full", "geometries": "geojson", "steps": "true"})
    except httpx.HTTPError as exc:
        raise upstream_unavailable("Could not reach the routing provider. Please try again shortly.") from exc

    if response.status_code != 200:
        raise upstream_unavailable(f"Routing provider returned an unexpected status ({response.status_code}).")

    data = response.json()
    if data.get("code") != "Ok" or not data.get("routes"):
        raise not_found("No route could be found between the given points.")

    route = data["routes"][0]
    steps: list[RouteStep] = []
    for leg in route.get("legs", []):
        for step in leg.get("steps", []):
            steps.append(
                RouteStep(
                    instruction=_describe_step(step.get("maneuver", {}), step.get("name", "")),
                    distance_meters=step.get("distance", 0.0),
                    duration_seconds=step.get("duration", 0.0),
                )
            )

    return DirectionsResponse(
        profile=req.profile,
        distance_meters=route["distance"],
        duration_seconds=route["duration"],
        geometry=route["geometry"]["coordinates"],
        steps=steps,
    )
