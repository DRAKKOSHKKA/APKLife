from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

SEARCH_URL = "https://it-institut.ru/SearchString/KeySearch"
SCHEDULE_URL_TEMPLATE = (
    "https://it-institut.ru/Raspisanie/SearchedRaspisanie"
    "?SearchId={search_id}&SearchString={search_string}&Type={entity_type}&OwnerId={owner_id}&WeekId={week_id}"
)
REQUEST_TIMEOUT_SECONDS = 30
CACHE_DIR = Path("cache")
CACHE_FILE = CACHE_DIR / "schedule_cache.json"


import requests

from services.cache_store import build_cache_key, get_schedule_cache, read_cache_data, upsert_schedule_cache
from services.constants import REQUEST_TIMEOUT_SECONDS, SCHEDULE_URL_TEMPLATE, SEARCH_URL
from services.schedule_parser import parse_schedule_html
from services.validators import normalize_search_string, validate_entity_info


def get_current_day_name():
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
    today = datetime.now()
    epoch = datetime(1970, 1, 1)
    days_since_epoch = (today - epoch).days
    return (days_since_epoch // 7) + 11659


def get_cached_entity_info(search_string):
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
    return {
        "SearchId": result.get("SearchId"),
        "SearchString": result.get("SearchContent"),
        "OwnerId": result.get("OwnerId"),
        "Type": result.get("Type"),
    }


def get_group_info(search_string):
    search_string = normalize_search_string(search_string)
    params = {"Id": 37, "SearchProductName": search_string}

    try:
        response = requests.get(SEARCH_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except (requests.exceptions.RequestException, ValueError) as error:
        print(f"Ошибка при поиске: {error}")
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
    return SCHEDULE_URL_TEMPLATE.format(
        search_id=entity_info["SearchId"],
        search_string=entity_info["SearchString"].replace(" ", "%20"),
        owner_id=entity_info["OwnerId"],
        entity_type=entity_info["Type"],
        week_id=week_id,
    )


def _network_source_meta():
    return {
        "source": "network",
        "cache_updated_at": datetime.now().isoformat(timespec="seconds"),
        "message": "Актуальные данные загружены из интернета.",
    }


def _cache_source_meta(updated_at):
    return {
        "source": "cache",
        "cache_updated_at": updated_at,
        "message": "Нет соединения с сайтом расписания. Показана сохранённая локальная версия.",
    }


def _empty_source_meta():
    return {
        "source": "none",
        "cache_updated_at": None,
        "message": "Не удалось загрузить расписание из интернета и локальный кэш отсутствует.",
    }


def get_schedule(week_id, entity_info):
    if not validate_entity_info(entity_info):
        return {}, [], None, None, {
            "source": "none",
            "cache_updated_at": None,
            "message": "Данные для загрузки не указаны.",
        }

    cache_key = build_cache_key(entity_info["SearchId"], week_id)

    try:
        response = requests.get(_build_schedule_url(week_id, entity_info), timeout=REQUEST_TIMEOUT_SECONDS)
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
        return schedule, days_list, prev_week_id, next_week_id, _network_source_meta()
    except requests.exceptions.RequestException as error:
        print(f"Ошибка при загрузке расписания из сети: {error}")

    cache_entry = get_schedule_cache(cache_key)
    if cache_entry:
        return (
            cache_entry.get("schedule", {}),
            cache_entry.get("days_list", []),
            cache_entry.get("prev_week_id"),
            cache_entry.get("next_week_id"),
            _cache_source_meta(cache_entry.get("updated_at")),
        )

    return {}, [], None, None, _empty_source_meta()
