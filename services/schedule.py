"""Schedule context builder for UI templates and API refresh endpoint."""

from __future__ import annotations

import datetime
from typing import Any

from services.cache_store import build_cache_key, get_schedule_cache
from services.exceptions import ScheduleError
from services.i18n import tr
from services.metrics import snapshot
from services.runtime_state import mark_error, mark_success
from services.utils_schedule import (
    cache_state_for,
    fetch_network_schedule,
    get_cached_entity_info,
    get_current_week,
    get_group_info,
    get_schedule,
    internet_available,
)


def build_base_context() -> dict[str, Any]:
    """Create default template context values."""
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
        "schedule_source": None,
        "schedule_message": None,
        "cache_updated_at": None,
        "offline": False,
        "cache_state": "missing",
        "cache_history": [],
        "warning": None,
        "error_type": None,
        "metrics": {},
    }


def detect_active_day(schedule: dict[str, Any], day_param: str | None) -> str | None:
    if not schedule:
        return None

    if day_param:
        for day in schedule.keys():
            if day.startswith(day_param):
                return day

    weekday = datetime.datetime.now().weekday()
    ru_days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    today = ru_days[weekday]

    for day in schedule.keys():
        if day.startswith(today):
            return day

    return next(iter(schedule))


def _resolve_entity(group_name: str):
    entity_info, corrected_name = get_group_info(group_name)
    if entity_info:
        return entity_info, corrected_name

    cached_entity = get_cached_entity_info(group_name)
    if cached_entity:
        return cached_entity, cached_entity.get("SearchString")

    return None, None


def _with_cache_state(context: dict[str, Any], week_id: int, entity_info: dict[str, object] | None):
    if not entity_info:
        return context
    key = build_cache_key(entity_info["SearchId"], week_id)
    cache_entry = get_schedule_cache(key)
    if cache_entry:
        context["cache_state"] = cache_state_for(entity_info, week_id)
        context["cache_history"] = list(reversed(cache_entry.get("history", [])[-5:]))
    else:
        context["cache_state"] = "missing"
        context["cache_history"] = []
    return context


def load_schedule_context(args):
    """Build context for /group page with cache-first loading behavior."""
    context = build_base_context()

    group_name = (args.get("group_name") or "").strip()
    week_id = args.get("week_id", type=int)
    day = args.get("day")

    context["week_id"] = week_id

    if not group_name:
        context["error"] = tr("group_required")
        return context

    entity_info, corrected_name = _resolve_entity(group_name)
    if not entity_info:
        context["error"] = tr("group_not_found", name=group_name)
        return context

    force_refresh = args.get("force_refresh") == "1"
    schedule, days_list, prev_week, next_week, source_meta = get_schedule(
        week_id or get_current_week(),
        entity_info,
        prefer_cache=not force_refresh,
    )

    active_day = detect_active_day(schedule, day)
    if active_day:
        schedule = {active_day: schedule[active_day]}

    context.update(
        {
            "group_info": entity_info,
            "schedule": schedule,
            "days_list": days_list,
            "prev_week_id": prev_week,
            "next_week_id": next_week,
            "active_day": active_day,
            "corrected_name": corrected_name,
            "no_lessons_week": not bool(schedule),
            "schedule_source": source_meta.get("source"),
            "schedule_message": source_meta.get("message"),
            "cache_updated_at": source_meta.get("cache_updated_at"),
            "offline": not internet_available(),
            "warning": source_meta.get("warning"),
            "error_type": source_meta.get("error_type"),
            "metrics": snapshot(),
        }
    )
    context = _with_cache_state(context, week_id or get_current_week(), entity_info)

    if not schedule:
        context["error"] = source_meta.get("message")
        mark_error(str(source_meta.get("message")))
    else:
        mark_success()
    return context


def force_refresh_context(args):
    """Force network refresh used by 'Обновить сейчас' action and AJAX refresh."""
    group_name = (args.get("group_name") or "").strip()
    week_id = args.get("week_id", type=int) or get_current_week()

    if not group_name:
        return build_base_context() | {"error": tr("group_required")}

    entity_info, corrected_name = _resolve_entity(group_name)
    if not entity_info:
        return build_base_context() | {"error": tr("group_not_found", name=group_name)}

    try:
        schedule, days_list, prev_week, next_week, source_meta = fetch_network_schedule(
            week_id, entity_info
        )
    except ScheduleError:
        schedule, days_list, prev_week, next_week, source_meta = get_schedule(
            week_id, entity_info, prefer_cache=True
        )

    active_day = detect_active_day(schedule, args.get("day"))
    if active_day:
        schedule = {active_day: schedule[active_day]}

    context = build_base_context()
    context.update(
        {
            "group_info": entity_info,
            "schedule": schedule,
            "days_list": days_list,
            "prev_week_id": prev_week,
            "next_week_id": next_week,
            "active_day": active_day,
            "corrected_name": corrected_name,
            "no_lessons_week": not bool(schedule),
            "week_id": week_id,
            "schedule_source": source_meta.get("source"),
            "schedule_message": source_meta.get("message"),
            "cache_updated_at": source_meta.get("cache_updated_at"),
            "warning": source_meta.get("warning"),
            "error_type": source_meta.get("error_type"),
            "error": source_meta.get("message") if not schedule else None,
            "offline": not internet_available(),
            "metrics": snapshot(),
        }
    )
    context = _with_cache_state(context, week_id, entity_info)
    if schedule:
        mark_success()
    else:
        mark_error(str(context.get("error")))
    return context
