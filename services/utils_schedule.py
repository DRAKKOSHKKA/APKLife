"""Main schedule integration service with cache-first and network-refresh strategies."""

from datetime import datetime
from time import perf_counter

import requests

from services.cache_store import (
    build_cache_key,
    get_schedule_cache,
    read_cache_data,
    upsert_schedule_cache,
)
from services.constants import (
    INTERNET_CHECK_TIMEOUT_SECONDS,
    INTERNET_CHECK_URL,
    REQUEST_TIMEOUT_SECONDS,
    SCHEDULE_URL_TEMPLATE,
    SEARCH_URL,
)
from services.logger import setup_logger
from services.metrics import inc, mark_source, set_value
from services.schedule_parser import parse_schedule_html
from services.validators import normalize_search_string, validate_entity_info

logger = setup_logger("schedule")


def get_current_day_name():
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


def get_current_week():
    """Return current week id according to source platform formula."""
    today = datetime.now()
    epoch = datetime(1970, 1, 1)
    days_since_epoch = (today - epoch).days
    return (days_since_epoch // 7) + 11659


def internet_available():
    """Fast internet availability check (Google 204 endpoint)."""
    inc("internet_checks_total")
    try:
        response = requests.get(INTERNET_CHECK_URL, timeout=INTERNET_CHECK_TIMEOUT_SECONDS)
        is_online = response.status_code in (200, 204)
        inc("internet_online" if is_online else "internet_offline")
        logger.info("Internet check status=%s code=%s", is_online, response.status_code)
        return is_online
    except requests.RequestException as error:
        inc("internet_offline")
        logger.warning("Internet check failed: %s", error)
        return False


def get_cached_entity_info(search_string):
    """Find matching entity info by normalized search string in local cache."""
    normalized = normalize_search_string(search_string).lower()
    if not normalized:
        return None

    cache_data = read_cache_data()
    for entry in cache_data.get("entries", {}).values():
        entity_info = entry.get("entity_info") or {}
        entity_name = normalize_search_string(entity_info.get("SearchString", "")).lower()
        if entity_name == normalized and validate_entity_info(entity_info):
            return entity_info
    return None


def _map_entity_result(result):
    """Map source search response payload to internal entity schema."""
    return {
        "SearchId": result.get("SearchId"),
        "SearchString": result.get("SearchContent"),
        "OwnerId": result.get("OwnerId"),
        "Type": result.get("Type"),
    }


def get_group_info(search_string):
    """Resolve search string into source entity metadata."""
    search_string = normalize_search_string(search_string)
    params = {"Id": 37, "SearchProductName": search_string}

    try:
        response = requests.get(SEARCH_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except (requests.exceptions.RequestException, ValueError) as error:
        logger.warning("Group search failed: %s", error)
        return None, None

    if not data:
        return None, None

    for result in data:
        if normalize_search_string(result.get("SearchContent", "")).lower() == search_string.lower():
            entity = _map_entity_result(result)
            return (entity, None) if validate_entity_info(entity) else (None, None)

    first_result = data[0]
    entity = _map_entity_result(first_result)
    corrected = first_result.get("SearchContent")
    return (entity, corrected) if validate_entity_info(entity) else (None, None)


def _build_schedule_url(week_id, entity_info):
    """Build source schedule URL from entity/week metadata."""
    return SCHEDULE_URL_TEMPLATE.format(
        search_id=entity_info["SearchId"],
        search_string=entity_info["SearchString"].replace(" ", "%20"),
        owner_id=entity_info["OwnerId"],
        entity_type=entity_info["Type"],
        week_id=week_id,
    )


def _network_source_meta(message="Актуальные данные загружены из интернета."):
    return {
        "source": "network",
        "cache_updated_at": datetime.now().isoformat(timespec="seconds"),
        "message": message,
    }


def _cache_source_meta(updated_at):
    return {
        "source": "cache",
        "cache_updated_at": updated_at,
        "message": "Показана сохранённая локальная версия. Выполняется фоновая проверка обновления.",
    }


def _empty_source_meta():
    return {
        "source": "none",
        "cache_updated_at": None,
        "message": "Не удалось загрузить расписание из интернета и локальный кэш отсутствует.",
    }


def fetch_network_schedule(week_id, entity_info):
    """Fetch schedule from remote source and update local cache."""
    inc("requests_total")
    if not validate_entity_info(entity_info):
        return {}, [], None, None, _empty_source_meta()

    cache_key = build_cache_key(entity_info["SearchId"], week_id)
    started = perf_counter()

    try:
        response = requests.get(
            _build_schedule_url(week_id, entity_info),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        response.encoding = "utf-8"

        schedule, days_list, prev_week_id, next_week_id = parse_schedule_html(response.text)
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
            "Network schedule fetched: group=%s week=%s latency_ms=%s lessons_days=%s",
            entity_info["SearchString"],
            week_id,
            latency_ms,
            len(schedule),
        )
        return schedule, days_list, prev_week_id, next_week_id, _network_source_meta()
    except requests.exceptions.RequestException as error:
        inc("network_fetch_error")
        latency_ms = round((perf_counter() - started) * 1000, 2)
        set_value("last_network_latency_ms", latency_ms)
        logger.warning(
            "Schedule fetch failed: group=%s week=%s latency_ms=%s error=%s",
            entity_info.get("SearchString"),
            week_id,
            latency_ms,
            error,
        )
        return {}, [], None, None, _empty_source_meta()


def get_schedule(week_id, entity_info, prefer_cache=True):
    """Get schedule with cache-first strategy and optional network fallback.

    If cache exists, return it immediately to avoid user waiting.
    Background update can be requested separately via refresh endpoint.
    """
    inc("requests_total")
    if not validate_entity_info(entity_info):
        return {}, [], None, None, {
            "source": "none",
            "cache_updated_at": None,
            "message": "Данные для загрузки не указаны.",
        }

    cache_key = build_cache_key(entity_info["SearchId"], week_id)
    cache_entry = get_schedule_cache(cache_key)

    if prefer_cache and cache_entry:
        inc("cache_hits")
        mark_source("cache")
        logger.info("Cache-first response for %s week %s", entity_info["SearchString"], week_id)
        return (
            cache_entry.get("schedule", {}),
            cache_entry.get("days_list", []),
            cache_entry.get("prev_week_id"),
            cache_entry.get("next_week_id"),
            _cache_source_meta(cache_entry.get("updated_at")),
        )

    if cache_entry:
        inc("cache_hits")
    else:
        inc("cache_misses")

    has_internet = internet_available()
    if has_internet:
        network_result = fetch_network_schedule(week_id, entity_info)
        if network_result[0]:
            return network_result

    if cache_entry:
        mark_source("cache")
        logger.info("Fallback to cache for %s week %s", entity_info["SearchString"], week_id)
        return (
            cache_entry.get("schedule", {}),
            cache_entry.get("days_list", []),
            cache_entry.get("prev_week_id"),
            cache_entry.get("next_week_id"),
            _cache_source_meta(cache_entry.get("updated_at")),
        )

    network_result = fetch_network_schedule(week_id, entity_info)
    if network_result[0]:
        network_result[4]["message"] = "Кэш создан из онлайн-данных."
        return network_result

    mark_source("none")
    return {}, [], None, None, _empty_source_meta()
