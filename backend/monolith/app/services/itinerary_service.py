from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.core.errors import forbidden, not_found
from app.repositories.json_store import store
from app.schemas.models import Destination, Itinerary, ItineraryCreate


def _hydrate(record: dict, destinations_by_id: dict[str, dict]) -> Itinerary:
    items = []
    for item in record["items"]:
        destination_record = destinations_by_id.get(item["destination_id"])
        if destination_record is None:
            continue
        items.append(
            {
                **item,
                "destination": Destination.model_validate(destination_record),
            }
        )
    return Itinerary.model_validate({**record, "items": items})


async def create_itinerary(owner_id: str, payload: ItineraryCreate) -> Itinerary:
    def mutator(db: dict) -> dict:
        destination_ids = {d["id"] for d in db["destinations"]}
        for item in payload.items:
            if item.destination_id not in destination_ids:
                raise not_found(f"Unknown destination_id: {item.destination_id}")

        now = datetime.now(timezone.utc).isoformat()
        record = {
            "id": f"itn-{uuid.uuid4().hex[:12]}",
            "owner_id": owner_id,
            "title": payload.title,
            "start_date": payload.start_date.isoformat(),
            "end_date": payload.end_date.isoformat(),
            "items": [item.model_dump() for item in payload.items],
            "created_at": now,
            "updated_at": now,
        }
        db["itineraries"].append(record)
        return record

    record = await store.mutate(mutator)
    db = await store.read()
    destinations_by_id = {d["id"]: d for d in db["destinations"]}
    return _hydrate(record, destinations_by_id)


async def list_itineraries_for_owner(owner_id: str) -> list[Itinerary]:
    db = await store.read()
    destinations_by_id = {d["id"]: d for d in db["destinations"]}
    own = [r for r in db["itineraries"] if r["owner_id"] == owner_id]
    return [_hydrate(record, destinations_by_id) for record in own]


async def get_itinerary_for_owner(owner_id: str, itinerary_id: str) -> Itinerary:
    db = await store.read()
    record = next((r for r in db["itineraries"] if r["id"] == itinerary_id), None)
    if record is None:
        raise not_found("Itinerary not found.")
    if record["owner_id"] != owner_id:
        raise forbidden("This itinerary belongs to another user.")
    destinations_by_id = {d["id"]: d for d in db["destinations"]}
    return _hydrate(record, destinations_by_id)
