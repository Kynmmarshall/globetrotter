"""Synchronous internal call to the Recommendation Service to validate a
destination_id and fetch a display snapshot when an item is added.

Short timeout, no retries: if the Recommendation Service is unavailable,
adding a NEW item fails clearly, but reading an EXISTING itinerary never
depends on this call (see PROJECT_PLAN.md section 7) -- items already store
their own destination_snapshot.
"""

from __future__ import annotations

import httpx

from app.core.config import settings
from app.core.errors import bad_request, upstream_unavailable


async def fetch_destination_snapshot(destination_id: str) -> dict:
    url = f"{settings.recommendation_service_base_url}/api/v1/destinations/{destination_id}"
    try:
        async with httpx.AsyncClient(timeout=settings.recommendation_service_timeout_seconds) as client:
            response = await client.get(url)
    except httpx.HTTPError as exc:
        raise upstream_unavailable("Could not reach the destination catalogue. Please try again shortly.") from exc

    if response.status_code == 404:
        raise bad_request(f"No destination with id {destination_id!r}.")
    if response.status_code != 200:
        raise upstream_unavailable(f"Destination catalogue returned an unexpected status ({response.status_code}).")

    data = response.json()
    return {
        "destination_id": data["id"],
        "name": data["name"],
        "category": data["category"],
        "lat": data["lat"],
        "lng": data["lng"],
        "image": data["image"],
    }
