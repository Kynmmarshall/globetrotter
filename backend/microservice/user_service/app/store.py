"""A tiny JSON-file "database" for the User Service.

Same limitations as the Phase 1 monolith's json_store.py (see
backend/monolith/app/repositories/json_store.py): guarded by a single
in-process lock and intended to run behind exactly one worker process. Writes
go to a temp file and atomically replace the real file so a crash mid-write
cannot corrupt the store. Each microservice owns its OWN file -- still no
shared storage between services, just no Postgres underneath it either.

All datetime/date/time values are stored as ISO 8601 strings (via
`.isoformat()`); Pydantic response models with `datetime`/`date`/`time`
typed fields parse those strings back automatically.
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
        "users": [],
        "favourites": [],
        "refresh_sessions": [],
        "chat_messages": [],
        "chat_reports": [],
        "room_sequence_counters": {},
        "outbox_events": [],
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
        """Run `mutator(store) -> result` under the write lock and persist the store.

        Everything the mutator does to the store dict is part of one
        all-or-nothing write to disk, which is what lets service functions
        keep "domain change + outbox event" atomic without a real database
        transaction.
        """
        with _lock:
            store = _read_sync()
            result = mutator(store)
            _write_sync(store)
            return result


store = JsonStore()
