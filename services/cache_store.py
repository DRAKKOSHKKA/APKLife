import json
from datetime import datetime
from pathlib import Path

from services.validators import validate_cache_timestamp, validate_schedule_payload

CACHE_DIR = Path("cache")
CACHE_FILE = CACHE_DIR / "schedule_cache.json"


def _ensure_cache_dir():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def read_cache_data():
    if not CACHE_FILE.exists():
        return {"entries": {}}
    try:
        raw_data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"entries": {}}

    entries = raw_data.get("entries", {})
    if not isinstance(entries, dict):
        return {"entries": {}}

    normalized_entries = {}
    for key, entry in entries.items():
        if not isinstance(entry, dict):
            continue
        normalized_entries[key] = {
            "entity_info": entry.get("entity_info", {}),
            "week_id": entry.get("week_id"),
            "schedule": validate_schedule_payload(entry.get("schedule", {})),
            "days_list": entry.get("days_list", []),
            "prev_week_id": entry.get("prev_week_id"),
            "next_week_id": entry.get("next_week_id"),
            "updated_at": entry.get("updated_at"),
        }

    return {"entries": normalized_entries}


def write_cache_data(data):
    _ensure_cache_dir()
    CACHE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def build_cache_key(search_id, week_id):
    return f"{search_id}:{week_id}"


def upsert_schedule_cache(cache_key, payload):
    cache_data = read_cache_data()
    payload = dict(payload)
    payload["updated_at"] = datetime.now().isoformat(timespec="seconds")
    cache_data.setdefault("entries", {})[cache_key] = payload
    write_cache_data(cache_data)


def get_schedule_cache(cache_key):
    entry = read_cache_data().get("entries", {}).get(cache_key)
    if not entry:
        return None

    if not validate_cache_timestamp(entry.get("updated_at")):
        entry["updated_at"] = None

    entry["schedule"] = validate_schedule_payload(entry.get("schedule", {}))
    if not isinstance(entry.get("days_list"), list):
        entry["days_list"] = []
    return entry
