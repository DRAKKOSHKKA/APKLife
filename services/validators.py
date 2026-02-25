from datetime import datetime


def normalize_search_string(value):
    return (value or "").strip()


def validate_entity_info(entity_info):
    if not isinstance(entity_info, dict):
        return False
    required_keys = {"SearchId", "SearchString", "OwnerId", "Type"}
    if not required_keys.issubset(entity_info.keys()):
        return False
    return all(entity_info.get(key) for key in required_keys)


def validate_cache_timestamp(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def normalize_lesson(lesson):
    if not isinstance(lesson, dict):
        return {
            "time": None,
            "subject": None,
            "teacher": None,
            "room": None,
            "group": None,
        }
    return {
        "time": lesson.get("time"),
        "subject": lesson.get("subject"),
        "teacher": lesson.get("teacher"),
        "room": lesson.get("room"),
        "group": lesson.get("group"),
    }


def validate_schedule_payload(schedule):
    if not isinstance(schedule, dict):
        return {}

    validated = {}
    for day, lessons in schedule.items():
        if not isinstance(day, str) or not isinstance(lessons, list):
            continue

        normalized_lesson_groups = []
        for lesson_group in lessons:
            if not isinstance(lesson_group, list):
                continue
            normalized_lesson_groups.append([normalize_lesson(lesson) for lesson in lesson_group])

        if normalized_lesson_groups:
            validated[day] = normalized_lesson_groups

    return validated
