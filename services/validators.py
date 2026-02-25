"""Validation and normalization helpers for schedule-related payloads."""

from __future__ import annotations

from datetime import datetime

from services.normalize import normalize_search
from services.types import Lesson


def normalize_search_string(value: str | None) -> str:
    """Normalize user search input string."""
    return normalize_search(value)


def validate_entity_info(entity_info: dict[str, object] | None) -> bool:
    """Validate that entity descriptor contains required fields."""
    if not isinstance(entity_info, dict):
        return False
    required_keys = {"SearchId", "SearchString", "OwnerId", "Type"}
    if not required_keys.issubset(entity_info.keys()):
        return False
    return all(entity_info.get(key) for key in required_keys)


def validate_cache_timestamp(value: str | None):
    """Validate cache timestamp in ISO format."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def normalize_lesson(lesson: dict[str, object] | None) -> Lesson:
    """Normalize lesson payload and always return schema-compatible dict."""
    if not isinstance(lesson, dict):
        return {
            "time": None,
            "subject": None,
            "teacher": None,
            "room": None,
            "group": None,
        }
    return {
        "time": lesson.get("time") if isinstance(lesson.get("time"), str) else None,
        "subject": lesson.get("subject") if isinstance(lesson.get("subject"), str) else None,
        "teacher": lesson.get("teacher") if isinstance(lesson.get("teacher"), str) else None,
        "room": lesson.get("room") if isinstance(lesson.get("room"), str) else None,
        "group": lesson.get("group") if isinstance(lesson.get("group"), str) else None,
    }


def validate_schedule_payload(schedule: dict[str, object] | None) -> dict[str, list[list[Lesson]]]:
    """Validate nested schedule structure and normalize invalid fragments."""
    if not isinstance(schedule, dict):
        return {}

    validated: dict[str, list[list[Lesson]]] = {}
    for day, lessons in schedule.items():
        if not isinstance(day, str) or not isinstance(lessons, list):
            continue

        normalized_lesson_groups: list[list[Lesson]] = []
        for lesson_group in lessons:
            if not isinstance(lesson_group, list):
                continue
            normalized_lesson_groups.append([normalize_lesson(lesson) for lesson in lesson_group])

        if normalized_lesson_groups:
            validated[day] = normalized_lesson_groups

    return validated
