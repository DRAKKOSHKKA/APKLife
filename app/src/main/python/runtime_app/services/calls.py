"""
Service for managing the call schedule (bell schedule) and breaks.
"""

from datetime import datetime, timezone, timedelta
from typing import Any

# Правильное расписание звонков для будних дней
WEEKDAY_SCHEDULE = [
    ('lesson', 1, "08:00", "09:20"),
    ('break', 'Перемена', "09:20", "09:30"),
    ('lesson', 2, "09:30", "10:50"),
    ('break', 'Большая перемена', "10:50", "11:20"),
    ('lesson', 3, "11:20", "12:40"),
    ('break', 'Перемена', "12:40", "12:50"),
    ('lesson', 4, "12:50", "14:10"),
    ('break', 'Большая Перемена', "14:10", "14:25"),
    ('lesson', 5, "14:25", "15:45"),
    ('break', 'Перемена', "15:45", "15:50"),
    ('lesson', 6, "15:50", "17:10"),
    ('break', 'Перемена', "17:10", "17:15"),
    ('lesson', 7, "17:15", "18:35"),
    ('break', 'Перемена', "18:35", "18:40"),
    ('lesson', 8, "18:40", "20:00"),
]

# Расписание звонков для субботы (поверхностное заполнение, пары по 1 часу)
SATURDAY_SCHEDULE = [
    ('lesson', 1, "08:00", "09:00"),
    ('break', 'Перемена', "09:00", "09:05"),
    ('lesson', 2, "09:05", "10:05"),
    ('break', 'Большая перемена', "10:05", "10:20"),
    ('lesson', 3, "10:20", "11:20"),
    ('break', 'Перемена', "11:20", "11:25"),
    ('lesson', 4, "11:25", "12:25"),
    ('break', 'Перемена', "12:25", "12:30"),
    ('lesson', 5, "12:30", "13:30"),
    ('break', 'Перемена', "13:30", "13:35"),
    ('lesson', 6, "13:35", "14:35"),
]

def _process_schedule(schedule_list, current_total, now_msk):
    data = []
    active = None
    for item_type, label, start, end in schedule_list:
        sh, sm = map(int, start.split(":"))
        eh, em = map(int, end.split(":"))
        start_total = sh * 60 + sm
        end_total = eh * 60 + em
        is_active = start_total <= current_total < end_total
        time_left = end_total - current_total if is_active else None

        item = {
            "type": item_type,
            "label": label,
            "start": start,
            "end": end,
            "is_active": is_active,
            "time_left": time_left
        }

        if is_active:
            # Расчитываем точное время окончания для таймера
            end_dt = now_msk.replace(hour=eh, minute=em, second=0, microsecond=0)
            active = {**item, "end_iso": end_dt.isoformat()}

        data.append(item)
    return data, active

def get_calls_context(test_time: str | None = None) -> dict[str, Any]:
    """
    Returns the call schedule with information about active items and countdowns.
    """
    now_msk = datetime.now(timezone(timedelta(hours=3)))
    is_saturday = now_msk.weekday() == 5

    if test_time:
        try:
            h, m = map(int, test_time.split(":"))
            current_total = h * 60 + m
        except Exception:
            current_total = now_msk.hour * 60 + now_msk.minute
    else:
        current_total = now_msk.hour * 60 + now_msk.minute

    weekday_data, weekday_active = _process_schedule(WEEKDAY_SCHEDULE, current_total, now_msk)
    saturday_data, saturday_active = _process_schedule(SATURDAY_SCHEDULE, current_total, now_msk)

    active_item = saturday_active if is_saturday else weekday_active
    schedule_data = saturday_data if is_saturday else weekday_data

    return {
        "items": schedule_data,
        "active_item": active_item,
        "current_total_minutes": current_total,
        "weekday_items": weekday_data,
        "saturday_items": saturday_data
    }

    return {
        "items": schedule_data,
        "active_item": active_item,
        "current_total_minutes": current_total
    }
