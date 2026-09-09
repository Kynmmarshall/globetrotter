"""A tiny JSON-file "database" for the Recommendation Service.

Same pattern as the User Service's app/store.py (see that file's docstring
for the full rationale): single in-process lock, atomic temp-file-then-replace
writes, one JSON document per service.
"""

from __future__ import annotations

import json
import os
import tempfile
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, TypeVar

from app.core.config import settings

T = TypeVar("T")
_lock = threading.Lock()


def new_id() -> str:
    return str(uuid.uuid4())


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _empty_store() -> dict[str, Any]:
    return {
        "destinations": [],
        "user_preference_projections": [],
        "outbox_events": [],
        "processed_events": [],
    }


def _read_sync() -> dict[str, Any]:
    path: Path = settings.data_file
    if not path.exists():
        store = _empty_store()
        _write_sync(store)
        return store
    data = json.loads(path.read_text(encoding="utf-8"))
    for key, default in _empty_store().items():
        data.setdefault(key, default)
    return data


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
    """Thread-safe read and read-modify-write access to the single JSON document."""

    def read(self) -> dict[str, Any]:
        with _lock:
            return _read_sync()

    def mutate(self, mutator: Callable[[dict[str, Any]], T]) -> T:
        with _lock:
            store = _read_sync()
            result = mutator(store)
            _write_sync(store)
            return result


store = JsonStore()
