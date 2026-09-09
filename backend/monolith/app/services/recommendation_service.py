"""Simple, explainable tag-overlap recommendations for the monolith.

Not a machine-learning ranking system: it scores destinations by how many of
the user's declared interests match the destination's tags/category, which
keeps the "why am I seeing this" reason honest and easy to display.
"""

from __future__ import annotations

from app.repositories.json_store import store
from app.schemas.models import Destination, RecommendedDestination


async def recommend_for_user(interests: list[str], limit: int = 10) -> list[RecommendedDestination]:
    db = await store.read()
    interest_set = {i.lower() for i in interests}

    results: list[RecommendedDestination] = []
    for record in db["destinations"]:
        tags = {t.lower() for t in record.get("tags", [])}
        tags.add(record["category"].lower())
        overlap = interest_set & tags
        if interest_set and not overlap:
            continue
        score = (len(overlap) / len(interest_set)) if interest_set else 0.5
        reason = (
            f"Matches your interest in {', '.join(sorted(overlap))}"
            if overlap
            else "Popular destination in this city"
        )
        results.append(
            RecommendedDestination(
                destination=Destination.model_validate(record),
                reason=reason,
                score=round(score, 2),
            )
        )

    results.sort(key=lambda r: r.score, reverse=True)
    return results[:limit]
