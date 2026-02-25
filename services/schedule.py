import datetime

from services.cache_store import (
    load_entity_cache,
    load_schedule_cache,
    save_entity_cache,
    save_schedule_cache,
    schedule_cache_key,
)
from services.utils_schedule import get_group_info, get_schedule, get_current_week


def build_base_context():
    return {
        "group_info": None,
        "schedule": {},
        "days_list": [],
        "prev_week_id": None,
        "next_week_id": None,
        "active_day": None,
        "week_id": None,
        "error": None,
        "corrected_name": None,
        "no_lessons_week": True,
        "data_source": "online",
        "last_updated_at": None,
    }


def detect_active_day(schedule, day_param):
    if not schedule:
        return None

    if day_param:
        for day in schedule.keys():
            if day.startswith(day_param):
                return day

    weekday = datetime.datetime.now().weekday()
    ru_days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    today = ru_days[weekday]

    for day in schedule.keys():
        if day.startswith(today):
            return day

    return next(iter(schedule))


def _humanize_date(raw: str | None) -> str | None:
    if not raw:
        return None
    try:
        dt = datetime.datetime.fromisoformat(raw)
        return dt.strftime('%d.%m.%Y %H:%M')
    except ValueError:
        return raw


def _load_schedule_with_fallback(week_id: int, entity_info: dict):
    key = schedule_cache_key(entity_info, week_id)

    schedule, days_list, prev_week, next_week = get_schedule(
        week_id,
        entity_info,
        timeout=30,
    )

    if schedule:
        save_schedule_cache(key, schedule, days_list, prev_week, next_week)
        return {
            "schedule": schedule,
            "days_list": days_list,
            "prev_week": prev_week,
            "next_week": next_week,
            "data_source": "online",
            "last_updated_at": datetime.datetime.now().strftime('%d.%m.%Y %H:%M'),
        }

    cached = load_schedule_cache(key)
    if cached:
        return {
            "schedule": cached.get("schedule", {}),
            "days_list": cached.get("days_list", []),
            "prev_week": cached.get("prev_week"),
            "next_week": cached.get("next_week"),
            "data_source": "cache",
            "last_updated_at": _humanize_date(cached.get("updated_at")),
        }

    return {
        "schedule": {},
        "days_list": [],
        "prev_week": None,
        "next_week": None,
        "data_source": "unavailable",
        "last_updated_at": None,
    }


def load_schedule_context(args):
    context = build_base_context()

    group_name = args.get("group_name")
    week_id = args.get("week_id", type=int)
    day = args.get("day")

    context["week_id"] = week_id

    if not group_name:
        context["error"] = "Не указано название группы"
        return context

    entity_info, corrected_name = get_group_info(group_name)
    entity_source = "online"
    if entity_info:
        save_entity_cache(group_name, entity_info, corrected_name)
    else:
        cached_entity = load_entity_cache(group_name)
        if cached_entity:
            entity_info = cached_entity.get("entity_info")
            corrected_name = cached_entity.get("corrected_name")
            entity_source = "cache"
        else:
            context["error"] = (
                "Не удалось получить данные с сервера расписания. "
                "Проверьте интернет или попробуйте позже."
            )
            return context

    resolved_week = week_id or get_current_week()
    schedule_payload = _load_schedule_with_fallback(resolved_week, entity_info)

    active_day = detect_active_day(schedule_payload["schedule"], day)

    if active_day:
        schedule_payload["schedule"] = {active_day: schedule_payload["schedule"][active_day]}

    if not schedule_payload["schedule"] and schedule_payload["data_source"] == "unavailable":
        context["error"] = (
            "Сервер недоступен или отвечает слишком долго (более 30 секунд), "
            "а локальный кэш для выбранного расписания отсутствует."
        )

    context.update({
        "group_info": entity_info,
        "schedule": schedule_payload["schedule"],
        "days_list": schedule_payload["days_list"],
        "prev_week_id": schedule_payload["prev_week"],
        "next_week_id": schedule_payload["next_week"],
        "active_day": active_day,
        "corrected_name": corrected_name,
        "no_lessons_week": not bool(schedule_payload["schedule"]),
        "data_source": schedule_payload["data_source"],
        "last_updated_at": schedule_payload["last_updated_at"],
    })

    if entity_source == "cache" and context["data_source"] == "online":
        context["data_source"] = "cache"

    return context
