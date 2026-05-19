"""Persistent cache store for parsed schedule payloads and history snapshots."""

from __future__ import annotations

import json
from datetime import datetime

from services.config import settings
from services.logging_config import get_logger
from services.validators import validate_cache_timestamp, validate_schedule_payload

logger = get_logger(__name__)


def _ensure_cache_dir() -> None:
    settings.cache_dir.mkdir(parents=True, exist_ok=True)


def read_cache_data() -> dict[str, object]:
    """Read and normalize cache data from disk."""
    if not settings.cache_file.exists():
        return {"entries": {}}

    try:
        raw_data = json.loads(settings.cache_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        logger.exception("cache_read_failed")
        return {"entries": {}}

    entries = raw_data.get("entries", {})
    if not isinstance(entries, dict):
        return {"entries": {}}

    normalized_entries: dict[str, dict[str, object]] = {}
    for key, entry in entries.items():
        if not isinstance(entry, dict):
            continue
        normalized_entries[key] = {
            "entity_info": entry.get("entity_info", {}),
            "week_id": entry.get("week_id"),
            "schedule": validate_schedule_payload(entry.get("schedule")),
            "days_list": entry.get("days_list", []),
            "prev_week_id": entry.get("prev_week_id"),
            "next_week_id": entry.get("next_week_id"),
            "updated_at": entry.get("updated_at"),
            "history": entry.get("history", []),
        }

    return {"entries": normalized_entries}


def write_cache_data(data: dict[str, object]) -> None:
    """Write cache payload to disk."""
    _ensure_cache_dir()
    settings.cache_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def build_cache_key(search_id: object, week_id: int) -> str:
    """Build deterministic cache key for entity/week pair."""
    return f"{search_id}:{week_id}"


def _build_history_entry(
    previous_schedule: dict[str, object], new_schedule: dict[str, object]
) -> dict[str, object]:
    previous_days = set(previous_schedule.keys())
    new_days = set(new_schedule.keys())
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "added_days": sorted(list(new_days - previous_days)),
        "removed_days": sorted(list(previous_days - new_days)),
        "changed": previous_schedule != new_schedule,
    }


def upsert_schedule_cache(cache_key: str, payload: dict[str, object]) -> None:
    """Insert or update schedule cache record with change history snapshots."""
    cache_data = read_cache_data()
    entries = cache_data.setdefault("entries", {})
    if not isinstance(entries, dict):
        entries = {}
        cache_data["entries"] = entries

    previous = entries.get(cache_key, {}) if isinstance(entries.get(cache_key), dict) else {}
    previous_schedule = previous.get("schedule", {}) if isinstance(previous, dict) else {}
    history = previous.get("history", []) if isinstance(previous, dict) else []
    if not isinstance(history, list):
        history = []

    history.append(
        _build_history_entry(
            previous_schedule if isinstance(previous_schedule, dict) else {},
            payload.get("schedule", {}),
        )
    )
    payload["updated_at"] = datetime.now().isoformat(timespec="seconds")
    payload["history"] = history[-10:]
    entries[cache_key] = payload
    write_cache_data(cache_data)


def get_schedule_cache(cache_key: str) -> dict[str, object] | None:
    """Get normalized cached schedule entry by key."""
    entry = read_cache_data().get("entries", {}).get(cache_key)
    if not isinstance(entry, dict):
        return None

    if not validate_cache_timestamp(
        entry.get("updated_at") if isinstance(entry.get("updated_at"), str) else None
    ):
        entry["updated_at"] = None

    entry["schedule"] = validate_schedule_payload(entry.get("schedule"))
    if not isinstance(entry.get("days_list"), list):
        entry["days_list"] = []
    if not isinstance(entry.get("history"), list):
        entry["history"] = []
    return entry


def cache_size() -> int:
    """Return count of cache records."""
    entries = read_cache_data().get("entries", {})
    return len(entries) if isinstance(entries, dict) else 0
