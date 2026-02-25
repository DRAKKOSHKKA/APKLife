"""Main schedule integration service with cache-first and network-refresh strategies."""

from __future__ import annotations

from datetime import datetime
from time import perf_counter
from typing import Any

from services.cache_store import (
    build_cache_key,
    get_schedule_cache,
    read_cache_data,
    upsert_schedule_cache,
)
from services.config import settings
from services.exceptions import (
    ScheduleError,
    ScheduleFetchError,
    ScheduleParseError,
    ScheduleSchemaChangedError,
)
from services.http_client import http_client
from services.logger import setup_logger
from services.metrics import inc, mark_source, set_value
from services.sources.html_source import InstituteHtmlScheduleSource
from services.types import CacheMeta
from services.validators import normalize_search_string, validate_entity_info

logger = setup_logger("schedule")
source = InstituteHtmlScheduleSource()


def get_current_day_name() -> str:
    """Return current day name in Russian."""
    days_ru = {
        "Monday": "Понедельник",
        "Tuesday": "Вторник",
        "Wednesday": "Среда",
        "Thursday": "Четверг",
        "Friday": "Пятница",
        "Saturday": "Суббота",
        "Sunday": "Воскресенье",
    }
    return days_ru[datetime.now().strftime("%A")]


def get_current_week() -> int:
    """Return current week id according to source platform formula."""
    today = datetime.now()
    epoch = datetime(1970, 1, 1)
    return ((today - epoch).days // 7) + 11659


def internet_available() -> bool:
    """Fast internet availability check (Google 204 endpoint)."""
    inc("internet_checks_total")
    try:
        http_client.get_text(
            settings.internet_check_url,
            timeout=(
                settings.internet_check_timeout_seconds,
                settings.internet_check_timeout_seconds,
            ),
        )
        inc("internet_online")
        return True
    except ScheduleFetchError:
        inc("internet_offline")
        return False


def get_cached_entity_info(search_string: str) -> dict[str, object] | None:
    """Find matching entity info by normalized search string in local cache."""
    normalized = normalize_search_string(search_string).lower()
    if not normalized:
        return None

    cache_data = read_cache_data()
    entries = cache_data.get("entries", {})
    if not isinstance(entries, dict):
        return None

    for entry in entries.values():
        if not isinstance(entry, dict):
            continue
        entity_info = entry.get("entity_info")
        if not isinstance(entity_info, dict):
            continue
        entity_name = normalize_search_string(str(entity_info.get("SearchString", ""))).lower()
        if entity_name == normalized and validate_entity_info(entity_info):
            return entity_info
    return None


def _map_entity_result(result: dict[str, Any]) -> dict[str, object]:
    return {
        "SearchId": result.get("SearchId"),
        "SearchString": result.get("SearchContent"),
        "OwnerId": result.get("OwnerId"),
        "Type": result.get("Type"),
    }


def get_group_info(search_string: str) -> tuple[dict[str, object] | None, str | None]:
    """Resolve search string into source entity metadata."""
    search_string = normalize_search_string(search_string)
    params = {"Id": 37, "SearchProductName": search_string}

    try:
        data = http_client.get_json(settings.search_url, params=params)
    except ScheduleFetchError as error:
        logger.warning("group_search_failed error=%s", error)
        return None, None

    if not isinstance(data, list) or not data:
        return None, None

    for result in data:
        if not isinstance(result, dict):
            continue
        content = normalize_search_string(str(result.get("SearchContent", ""))).lower()
        if content == search_string.lower():
            entity = _map_entity_result(result)
            return (entity, None) if validate_entity_info(entity) else (None, None)

    first_result = data[0] if isinstance(data[0], dict) else {}
    entity = _map_entity_result(first_result)
    corrected = first_result.get("SearchContent") if isinstance(first_result, dict) else None
    return (entity, corrected) if validate_entity_info(entity) else (None, None)


def _meta(
    source_name: str,
    cache_updated_at: str | None,
    message: str,
    warning: str | None = None,
    error_type: str | None = None,
) -> CacheMeta:
    return {
        "source": source_name,  # type: ignore[typeddict-item]
        "cache_updated_at": cache_updated_at,
        "message": message,
        "warning": warning,
        "error_type": error_type,
    }


def fetch_network_schedule(week_id: int, entity_info: dict[str, object]):
    """Fetch schedule from remote source and update local cache."""
    inc("requests_total")
    if not validate_entity_info(entity_info):
        return (
            {},
            [],
            None,
            None,
            _meta("none", None, "Некорректные параметры группы.", error_type="validation"),
        )

    cache_key = build_cache_key(entity_info["SearchId"], week_id)
    started = perf_counter()

    try:
        html = source.fetch_html(week_id, entity_info)
        parsed = source.parse(html)
        schedule = parsed["schedule"]
        days_list = parsed["days_list"]
        prev_week_id = parsed["prev_week_id"]
        next_week_id = parsed["next_week_id"]
        upsert_schedule_cache(
            cache_key,
            {
                "entity_info": entity_info,
                "week_id": week_id,
                "schedule": schedule,
                "days_list": days_list,
                "prev_week_id": prev_week_id,
                "next_week_id": next_week_id,
            },
        )
        latency_ms = round((perf_counter() - started) * 1000, 2)
        inc("network_fetch_success")
        set_value("last_network_latency_ms", latency_ms)
        mark_source("network")
        logger.info(
            "network_schedule_success group=%s week=%s latency_ms=%s",
            entity_info["SearchString"],
            week_id,
            latency_ms,
        )
        return (
            schedule,
            days_list,
            prev_week_id,
            next_week_id,
            _meta(
                "network",
                datetime.now().isoformat(timespec="seconds"),
                "Актуальные данные загружены из интернета.",
            ),
        )
    except (ScheduleFetchError, ScheduleSchemaChangedError, ScheduleParseError) as error:
        inc("network_fetch_error")
        set_value("last_network_latency_ms", round((perf_counter() - started) * 1000, 2))
        logger.warning(
            "network_schedule_failed group=%s week=%s error=%s",
            entity_info.get("SearchString"),
            week_id,
            error,
        )
        raise
    except Exception as error:  # noqa: BLE001
        inc("network_fetch_error")
        logger.exception("unexpected_schedule_failure")
        raise ScheduleError("Unexpected schedule loading failure") from error


def get_schedule(week_id: int, entity_info: dict[str, object], prefer_cache: bool = True):
    """Get schedule with cache-first strategy and safe fallbacks."""
    if not validate_entity_info(entity_info):
        return (
            {},
            [],
            None,
            None,
            _meta("none", None, "Данные для загрузки не указаны.", error_type="validation"),
        )

    cache_key = build_cache_key(entity_info["SearchId"], week_id)
    cache_entry = get_schedule_cache(cache_key)

    if prefer_cache and cache_entry:
        inc("cache_hits")
        mark_source("cache")
        return (
            cache_entry.get("schedule", {}),
            cache_entry.get("days_list", []),
            cache_entry.get("prev_week_id"),
            cache_entry.get("next_week_id"),
            _meta(
                "cache",
                (
                    cache_entry.get("updated_at")
                    if isinstance(cache_entry.get("updated_at"), str)
                    else None
                ),
                "Показана сохранённая локальная версия.",
            ),
        )

    try:
        return fetch_network_schedule(week_id, entity_info)
    except (ScheduleFetchError, ScheduleParseError, ScheduleSchemaChangedError) as error:
        if cache_entry:
            mark_source("cache")
            return (
                cache_entry.get("schedule", {}),
                cache_entry.get("days_list", []),
                cache_entry.get("prev_week_id"),
                cache_entry.get("next_week_id"),
                _meta(
                    "cache",
                    (
                        cache_entry.get("updated_at")
                        if isinstance(cache_entry.get("updated_at"), str)
                        else None
                    ),
                    "Показана сохранённая локальная версия.",
                    warning="Source unavailable or structure changed. Showing cached data.",
                    error_type=error.__class__.__name__,
                ),
            )
        return (
            {},
            [],
            None,
            None,
            _meta(
                "none",
                None,
                "Не удалось получить расписание и кэш отсутствует.",
                warning="Source unavailable or structure changed. Showing cached data.",
                error_type=error.__class__.__name__,
            ),
        )


def cache_state_for(entity_info: dict[str, object] | None, week_id: int) -> str:
    if not entity_info or not validate_entity_info(entity_info):
        return "unknown"
    cache_key = build_cache_key(entity_info["SearchId"], week_id)
    return "hot" if get_schedule_cache(cache_key) else "empty"
