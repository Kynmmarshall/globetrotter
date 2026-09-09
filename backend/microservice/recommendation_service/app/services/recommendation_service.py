"""Personalized (or fallback) destination recommendations.

Personalization uses ONLY the local read-projection of User Service data
(app.models.UserPreferenceProjection), kept current via RabbitMQ events -- no
synchronous call back to the User Service (see PROJECT_PLAN.md section 7).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models import Destination
from app.repositories import destinations as destinations_repo
from app.repositories import preferences as preferences_repo
from app.store import store


@dataclass
class RankedDestination:
    destination: Destination
    reason: str


def _fallback_recommendations(destinations: list[Destination], limit: int) -> list[RankedDestination]:
    destinations = sorted(destinations, key=lambda d: d["name"])
    return [RankedDestination(destination=d, reason="Popular in Yaounde") for d in destinations[:limit]]


def get_recommendations(*, user_id: str | None, limit: int) -> tuple[list[RankedDestination], bool]:
    db = store.read()
    destinations = destinations_repo.list_all(db)

    if user_id is None:
        return _fallback_recommendations(destinations, limit), False

    projection = preferences_repo.get_projection(db, user_id)
    if projection is None or not projection["interests"]:
        return _fallback_recommendations(destinations, limit), False

    interests = {interest.lower() for interest in projection["interests"]}
    favourites = set(projection["favourite_destination_ids"] or [])

    scored: list[tuple[int, str, RankedDestination]] = []
    for destination in destinations:
        if destination["id"] in favourites:
            continue  # already saved -- recommend new places, not ones they have

        tags = {tag.lower() for tag in (destination["tags"] or [])}
        tags.add(destination["category"].lower())
        matched = tags & interests
        if not matched:
            continue

        reason = f"Matches your interest in {sorted(matched)[0].replace('-', ' ')}"
        scored.append((len(matched), destination["name"], RankedDestination(destination=destination, reason=reason)))

    if not scored:
        return _fallback_recommendations(destinations, limit), False

    scored.sort(key=lambda item: (-item[0], item[1]))
    return [item[2] for item in scored[:limit]], True
