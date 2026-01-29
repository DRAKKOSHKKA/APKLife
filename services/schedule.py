import datetime
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
    if not entity_info:
        context["error"] = f"'{group_name}' не найдено"
        return context

    schedule, days_list, prev_week, next_week = get_schedule(
        week_id or get_current_week(),
        entity_info
    )

    active_day = detect_active_day(schedule, day)

    if active_day:
        schedule = {active_day: schedule[active_day]}

    context.update({
        "group_info": entity_info,
        "schedule": schedule,
        "days_list": days_list,
        "prev_week_id": prev_week,
        "next_week_id": next_week,
        "active_day": active_day,
        "corrected_name": corrected_name,
        "no_lessons_week": not bool(schedule)
    })

    return context
