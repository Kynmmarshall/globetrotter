"""A tiny JSON-file "database" for the Phase 1 monolith.

Explicitly NOT a concurrent database: guarded by a single in-process asyncio
lock and intended to run behind exactly one Uvicorn worker. Writes go to a
temp file and are then moved into place so a crash mid-write cannot corrupt
the store. This preserves (and documents) the monolith's real limitations:
no transactions, no indexing, no multi-process safety.
"""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from app.core.config import settings

_lock = asyncio.Lock()


def _empty_store() -> dict[str, Any]:
    return {"users": [], "destinations": [], "itineraries": []}


def _load_seed_destinations() -> list[dict[str, Any]]:
    if settings.seed_destinations_file.exists():
        return json.loads(settings.seed_destinations_file.read_text(encoding="utf-8"))
    return []


def _read_sync() -> dict[str, Any]:
    path: Path = settings.data_file
    if not path.exists():
        store = _empty_store()
        store["destinations"] = _load_seed_destinations()
        _write_sync(store)
        return store
    return json.loads(path.read_text(encoding="utf-8"))


def _write_sync(store: dict[str, Any]) -> None:
    path: Path = settings.data_file
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), prefix=".db-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(store, handle, indent=2)
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


class JsonStore:
    """Async-safe read/modify/write access to the single JSON document."""

    async def read(self) -> dict[str, Any]:
        async with _lock:
            return _read_sync()

    async def mutate(self, mutator) -> Any:
        """Run `mutator(store) -> result` under the write lock and persist the store."""
        async with _lock:
            store = _read_sync()
            result = mutator(store)
            _write_sync(store)
            return result


store = JsonStore()
