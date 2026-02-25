"""HTML parser for schedule pages with schema guards and normalization."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime

from bs4 import BeautifulSoup

from services.config import settings
from services.exceptions import ScheduleParseError, ScheduleSchemaChangedError
from services.logging_config import get_logger
from services.normalize import normalize_optional, normalize_text
from services.types import Lesson, ScheduleResult

logger = get_logger(__name__)

EMPTY_LESSON: Lesson = {
    "time": None,
    "subject": None,
    "teacher": None,
    "room": None,
    "group": None,
}


def _save_failed_html(raw_html: str, reason: str) -> None:
    settings.failed_html_dir.mkdir(parents=True, exist_ok=True)
    html_hash = hashlib.sha256(raw_html.encode("utf-8", errors="ignore")).hexdigest()[:16]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = settings.failed_html_dir / f"{timestamp}_{html_hash}.html"
    path.write_text(raw_html, encoding="utf-8", errors="ignore")
    logger.error("schema_guard_failed reason=%s hash=%s path=%s", reason, html_hash, path)


def _validate_schema(soup: BeautifulSoup, raw_html: str) -> None:
    table = soup.find("table")
    thead = soup.find("thead")
    tbody = soup.find("tbody")
    if not table or not thead or not tbody:
        _save_failed_html(raw_html, "missing_table_or_sections")
        raise ScheduleSchemaChangedError("Missing required schedule table structure")

    header_rows = thead.find_all("tr")
    body_rows = tbody.find_all("tr")
    if not header_rows or not body_rows:
        _save_failed_html(raw_html, "missing_header_or_rows")
        raise ScheduleSchemaChangedError("Missing header rows or body rows")

    header_cells = header_rows[0].find_all(["th", "td"])
    if len(header_cells) < 2:
        _save_failed_html(raw_html, "insufficient_columns")
        raise ScheduleSchemaChangedError("Expected at least day column and one lesson column")

    first_header = normalize_text(header_cells[0].get_text(" ", strip=True), lower=True) or ""
    if "день" not in first_header and "day" not in first_header:
        _save_failed_html(raw_html, f"unexpected_header:{first_header}")
        raise ScheduleSchemaChangedError("Unexpected first header name")


def _time_to_minutes(time_str: str) -> int:
    hours, minutes = map(int, time_str.split(":"))
    return hours * 60 + minutes


def _minutes_to_time(minutes: int) -> str:
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"


def split_time_interval(time_range: str | None, num_parts: int) -> list[str | None]:
    """Split time range into N segments for merged lesson blocks."""
    if not time_range or "-" not in time_range or num_parts <= 0:
        return [time_range] * max(num_parts, 1)

    try:
        start_time, end_time = time_range.split("-")
        start_minutes = _time_to_minutes(start_time.strip())
        end_minutes = _time_to_minutes(end_time.strip())
    except (ValueError, TypeError) as exc:
        raise ScheduleParseError("Invalid time range format") from exc

    total_minutes = max(end_minutes - start_minutes, 1)
    part_minutes = max(total_minutes // num_parts, 1)

    intervals: list[str] = []
    for index in range(num_parts):
        part_start = start_minutes + index * part_minutes
        part_end = min(part_start + part_minutes, end_minutes)
        intervals.append(f"{_minutes_to_time(part_start)}-{_minutes_to_time(part_end)}")
    return intervals


def _parse_lesson_div(div, lesson_time: str | None) -> Lesson:
    spans = [normalize_optional(span.get_text(" ", strip=True)) for span in div.find_all("span")]
    teacher_room_full = spans[1] if len(spans) > 1 else None

    teacher = None
    room = None
    if teacher_room_full:
        parts = [normalize_optional(part) for part in teacher_room_full.split(",")]
        parts = [part for part in parts if part]
        if parts:
            teacher = parts[0]
        if len(parts) > 1:
            room = ", ".join(parts[1:])

    return {
        "time": normalize_optional(lesson_time),
        "subject": spans[0] if len(spans) > 0 else None,
        "teacher": teacher,
        "room": room,
        "group": spans[2] if len(spans) > 2 else None,
    }


def parse_schedule_html(html_text: str) -> ScheduleResult:
    """Parse source HTML into schedule map with strict schema validation."""
    try:
        soup = BeautifulSoup(html_text, "html.parser")
        _validate_schema(soup, html_text)

        header_rows = soup.select("thead tr")
        time_headers: list[str] = []
        for th in header_rows[0].find_all("th")[1:]:
            value = normalize_optional(th.get_text(" ", strip=True))
            if not value:
                continue
            time_headers.extend([value] * int(th.get("colspan", 1)))

        schedule: dict[str, list[list[Lesson]]] = {}
        days_list: list[str] = []

        for row in soup.select("tbody tr"):
            day_cell = row.find("th")
            if not day_cell:
                continue

            day_text = normalize_optional(day_cell.get_text(" ", strip=True))
            if not day_text:
                continue
            days_list.append(day_text)
            lessons_for_day: list[list[Lesson]] = []
            all_cells: list[dict[str, object]] = []
            time_index = 0

            for td in row.find_all("td"):
                colspan = int(td.get("colspan", 1))
                current_time_range = (
                    time_headers[time_index] if time_index < len(time_headers) else None
                )
                lesson_divs = td.find_all("div")

                if lesson_divs:
                    time_intervals = split_time_interval(current_time_range, len(lesson_divs))
                    lessons = [
                        _parse_lesson_div(div, time_intervals[idx])
                        for idx, div in enumerate(lesson_divs)
                    ]
                    all_cells.append({"lessons": lessons, "time_range": current_time_range})
                else:
                    all_cells.append({"lessons": [], "time_range": current_time_range})

                time_index += colspan

            last_filled_index = -1
            for idx, cell in enumerate(all_cells):
                if cell["lessons"]:
                    last_filled_index = idx

            for idx, cell in enumerate(all_cells):
                if idx > last_filled_index and last_filled_index != -1:
                    break
                if cell["lessons"]:
                    lessons_for_day.append(cell["lessons"])
                else:
                    empty: Lesson = {**EMPTY_LESSON}
                    empty["time"] = normalize_optional(cell["time_range"])
                    lessons_for_day.append([empty])

            if lessons_for_day:
                schedule[day_text] = lessons_for_day

        prev_week_id = None
        next_week_id = None
        current_week_link = soup.find("a", class_="btn-primary")

        if current_week_link:
            prev_link = current_week_link.find_previous_sibling("a")
            if prev_link and "href" in prev_link.attrs:
                match = re.search(r"WeekId=(\d+)", prev_link["href"])
                if match:
                    prev_week_id = int(match.group(1))

            next_link = current_week_link.find_next_sibling("a")
            if next_link and "href" in next_link.attrs:
                match = re.search(r"WeekId=(\d+)", next_link["href"])
                if match:
                    next_week_id = int(match.group(1))

        return {
            "schedule": schedule,
            "days_list": days_list,
            "prev_week_id": prev_week_id,
            "next_week_id": next_week_id,
        }
    except ScheduleSchemaChangedError:
        raise
    except ScheduleParseError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("schedule_parse_error")
        raise ScheduleParseError("Unable to parse schedule HTML") from exc
