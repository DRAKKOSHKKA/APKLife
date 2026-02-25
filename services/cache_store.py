from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

CACHE_DIR = Path("data/cache")
SCHEDULE_CACHE_FILE = CACHE_DIR / "schedule_cache.json"
VERSION_CACHE_FILE = CACHE_DIR / "version_cache.json"


def ensure_cache_dir() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    ensure_cache_dir()
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def schedule_cache_key(entity_info: Dict[str, Any], week_id: int) -> str:
    raw = (
        f"{entity_info.get('SearchId')}|{entity_info.get('SearchString')}|"
        f"{entity_info.get('OwnerId')}|{entity_info.get('Type')}|{week_id}"
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def save_schedule_cache(
    key: str,
    schedule: Dict[str, Any],
    days_list: list,
    prev_week: Optional[int],
    next_week: Optional[int],
) -> None:
    payload = _read_json(SCHEDULE_CACHE_FILE)
    payload[key] = {
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "schedule": schedule,
        "days_list": days_list,
        "prev_week": prev_week,
        "next_week": next_week,
    }
    _write_json(SCHEDULE_CACHE_FILE, payload)


def load_schedule_cache(key: str) -> Optional[Dict[str, Any]]:
    payload = _read_json(SCHEDULE_CACHE_FILE)
    cached = payload.get(key)
    if not cached:
        return None
    return cached


def load_version_cache() -> Dict[str, Any]:
    return _read_json(VERSION_CACHE_FILE)


def save_version_cache(data: Dict[str, Any]) -> None:
    _write_json(VERSION_CACHE_FILE, data)


ENTITY_CACHE_FILE = CACHE_DIR / "entity_cache.json"


def _normalize_query(query: str) -> str:
    return (query or "").strip().lower()


def save_entity_cache(query: str, entity_info: Dict[str, Any], corrected_name: Optional[str]) -> None:
    payload = _read_json(ENTITY_CACHE_FILE)
    payload[_normalize_query(query)] = {
        "entity_info": entity_info,
        "corrected_name": corrected_name,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    _write_json(ENTITY_CACHE_FILE, payload)


def load_entity_cache(query: str) -> Optional[Dict[str, Any]]:
    payload = _read_json(ENTITY_CACHE_FILE)
    return payload.get(_normalize_query(query))
