"""In-memory metrics collector for diagnostics and DEV mode."""

from __future__ import annotations

from datetime import datetime
from threading import Lock

_METRICS = {
    "requests_total": 0,
    "network_fetch_success": 0,
    "network_fetch_error": 0,
    "cache_hits": 0,
    "cache_misses": 0,
    "internet_checks_total": 0,
    "internet_online": 0,
    "internet_offline": 0,
    "last_network_latency_ms": None,
    "last_schedule_source": None,
    "last_updated_at": None,
}
_LOCK = Lock()


def inc(key: str, value: int = 1) -> None:
    with _LOCK:
        _METRICS[key] = int(_METRICS.get(key, 0)) + value


def set_value(key: str, value) -> None:
    with _LOCK:
        _METRICS[key] = value


def mark_source(source: str) -> None:
    with _LOCK:
        _METRICS["last_schedule_source"] = source
        _METRICS["last_updated_at"] = datetime.now().isoformat(timespec="seconds")


def snapshot() -> dict:
    with _LOCK:
        return dict(_METRICS)
