"""Plain-dict access to itinerary share links."""

from __future__ import annotations

import secrets
from typing import Any

from app.models import ShareLink
from app.store import new_id, now_iso


def create_or_replace(db: dict[str, Any], itinerary_id: str, existing: ShareLink | None) -> ShareLink:
    if existing is not None:
        db["share_links"].remove(existing)

    share: ShareLink = {
        "id": new_id(),
        "itinerary_id": itinerary_id,
        "token": secrets.token_urlsafe(24),
        "created_at": now_iso(),
        "revoked_at": None,
    }
    db["share_links"].append(share)
    return share


def revoke(db: dict[str, Any], share: ShareLink) -> None:
    share["revoked_at"] = now_iso()
