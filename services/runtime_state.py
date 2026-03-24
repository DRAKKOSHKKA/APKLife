"""Runtime mutable state for health checks and diagnostics."""

from __future__ import annotations

from datetime import datetime
from threading import Lock

_STATE = {
    "started_at": datetime.now().isoformat(timespec="seconds"),
    "last_successful_update": None,
    "last_error": None,
}
_LOCK = Lock()


def mark_success() -> None:
    with _LOCK:
        _STATE["last_successful_update"] = datetime.now().isoformat(timespec="seconds")
        _STATE["last_error"] = None


def mark_error(message: str) -> None:
    with _LOCK:
        _STATE["last_error"] = message


def snapshot_state() -> dict[str, str | None]:
    with _LOCK:
        return dict(_STATE)
