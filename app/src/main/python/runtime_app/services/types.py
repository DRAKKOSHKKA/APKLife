"""Typed structures for schedule domain payloads."""

from __future__ import annotations

from typing import Literal, TypedDict


class Lesson(TypedDict):
    time: str | None
    subject: str | None
    teacher: str | None
    room: str | None
    group: str | None


class DaySchedule(TypedDict):
    day: str
    lessons: list[list[Lesson]]


class CacheMeta(TypedDict):
    source: Literal["network", "cache", "none"]
    cache_updated_at: str | None
    message: str
    warning: str | None
    error_type: str | None


class ScheduleResult(TypedDict):
    schedule: dict[str, list[list[Lesson]]]
    days_list: list[str]
    prev_week_id: int | None
    next_week_id: int | None
