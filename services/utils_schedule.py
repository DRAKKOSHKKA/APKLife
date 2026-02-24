import json
import re
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


def _ensure_cache_dir():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _read_cache_data():
    if not CACHE_FILE.exists():
        return {"entries": {}}
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"entries": {}}


def _write_cache_data(data):
    _ensure_cache_dir()
    CACHE_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _cache_key(search_id, week_id):
    return f"{search_id}:{week_id}"


def get_cached_entity_info(search_string):
    normalized = (search_string or "").strip().lower()
    if not normalized:
        return None

    cache_data = _read_cache_data()
    for entry in cache_data.get("entries", {}).values():
        entity_info = entry.get("entity_info") or {}
        entity_name = (entity_info.get("SearchString") or "").strip().lower()
        if entity_name == normalized:
            return entity_info
    return None


def get_group_info(search_string):
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
        if result.get("SearchContent", "").lower() == search_string.lower():
            return {
                "SearchId": result.get("SearchId"),
                "SearchString": result.get("SearchContent"),
                "OwnerId": result.get("OwnerId"),
                "Type": result.get("Type"),
            }, None

    first_result = data[0]
    return {
        "SearchId": first_result.get("SearchId"),
        "SearchString": first_result.get("SearchContent"),
        "OwnerId": first_result.get("OwnerId"),
        "Type": first_result.get("Type"),
    }, first_result.get("SearchContent")


def _split_time_interval(time_range, num_parts):
    if not time_range or "-" not in time_range:
        return [time_range] * num_parts

    def time_to_minutes(time_str):
        hours, minutes = map(int, time_str.split(":"))
        return hours * 60 + minutes

    def minutes_to_time(minutes):
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"

    try:
        start_time, end_time = time_range.split("-")
        start_minutes = time_to_minutes(start_time.strip())
        end_minutes = time_to_minutes(end_time.strip())
    except (ValueError, TypeError):
        return [time_range] * num_parts

    total_minutes = end_minutes - start_minutes
    part_minutes = max(total_minutes // num_parts, 1)
    intervals = []
    for index in range(num_parts):
        part_start = start_minutes + index * part_minutes
        part_end = part_start + part_minutes
        intervals.append(f"{minutes_to_time(part_start)}-{minutes_to_time(part_end)}")
    return intervals


def _parse_schedule_html(html_text):
    soup = BeautifulSoup(html_text, "html.parser")

    time_headers = []
    header_rows = soup.select("thead tr")
    if not header_rows:
        return {}, [], None, None

    for th in header_rows[0].find_all("th")[1:]:
        colspan = int(th.get("colspan", 1))
        time_text = th.get_text(strip=True)
        time_headers.extend([time_text] * colspan)

    schedule = {}
    days_list = []

    for row in soup.select("tbody tr"):
        day_cell = row.find("th")
        if not day_cell:
            continue

        day_text = day_cell.get_text(" ", strip=True)
        days_list.append(day_text)
        lessons_for_day = []
        time_index = 0
        all_cells = []

        for td in row.find_all("td"):
            colspan = int(td.get("colspan", 1))
            current_time_range = time_headers[time_index] if time_index < len(time_headers) else None
            lesson_divs = td.find_all("div")

            if lesson_divs:
                time_intervals = _split_time_interval(current_time_range, len(lesson_divs))
                lessons_in_cell = []
                for lesson_index, div in enumerate(lesson_divs):
                    spans = [span.get_text(strip=True) for span in div.find_all("span")]
                    teacher_room_full = spans[1] if len(spans) > 1 else None
                    teacher = None
                    room = None

                    if teacher_room_full:
                        parts = [part.strip() for part in teacher_room_full.split(",") if part.strip()]
                        if len(parts) == 1:
                            teacher = parts[0]
                        elif len(parts) >= 2:
                            teacher = parts[0]
                            room = ", ".join(parts[1:])

                    lessons_in_cell.append(
                        {
                            "time": time_intervals[lesson_index]
                            if lesson_index < len(time_intervals)
                            else current_time_range,
                            "subject": spans[0] if len(spans) > 0 else None,
                            "teacher": teacher,
                            "room": room,
                            "group": spans[2] if len(spans) > 2 else None,
                        }
                    )

                all_cells.append({"lessons": lessons_in_cell, "time_range": current_time_range})
            else:
                all_cells.append({"lessons": [], "time_range": current_time_range})

            time_index += colspan

        last_lesson_index = -1
        for index, cell in enumerate(all_cells):
            if cell["lessons"]:
                last_lesson_index = index

        for index, cell in enumerate(all_cells):
            if index > last_lesson_index and last_lesson_index != -1:
                break

            if cell["lessons"]:
                lessons_for_day.append(cell["lessons"])
            else:
                lessons_for_day.append(
                    [
                        {
                            "time": cell["time_range"],
                            "subject": None,
                            "teacher": None,
                            "room": None,
                            "group": None,
                        }
                    ]
                )

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

    return schedule, days_list, prev_week_id, next_week_id


def _cache_schedule(week_id, entity_info, schedule, days_list, prev_week_id, next_week_id):
    cache_data = _read_cache_data()
    key = _cache_key(entity_info["SearchId"], week_id)
    cache_data.setdefault("entries", {})[key] = {
        "entity_info": entity_info,
        "week_id": week_id,
        "schedule": schedule,
        "days_list": days_list,
        "prev_week_id": prev_week_id,
        "next_week_id": next_week_id,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    _write_cache_data(cache_data)


def _get_cached_schedule(week_id, entity_info):
    cache_data = _read_cache_data()
    key = _cache_key(entity_info["SearchId"], week_id)
    entry = cache_data.get("entries", {}).get(key)
    if not entry:
        return None

    return {
        "schedule": entry.get("schedule", {}),
        "days_list": entry.get("days_list", []),
        "prev_week_id": entry.get("prev_week_id"),
        "next_week_id": entry.get("next_week_id"),
        "updated_at": entry.get("updated_at"),
    }


def get_schedule(week_id, entity_info):
    if not entity_info:
        return {}, [], None, None, {
            "source": "none",
            "cache_updated_at": None,
            "message": "Данные для загрузки не указаны.",
        }

    url = SCHEDULE_URL_TEMPLATE.format(
        search_id=entity_info["SearchId"],
        search_string=entity_info["SearchString"].replace(" ", "%20"),
        owner_id=entity_info["OwnerId"],
        entity_type=entity_info["Type"],
        week_id=week_id,
    )

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        response.encoding = "utf-8"
        schedule, days_list, prev_week_id, next_week_id = _parse_schedule_html(response.text)
        _cache_schedule(week_id, entity_info, schedule, days_list, prev_week_id, next_week_id)
        return schedule, days_list, prev_week_id, next_week_id, {
            "source": "network",
            "cache_updated_at": datetime.now().isoformat(timespec="seconds"),
            "message": "Актуальные данные загружены из интернета.",
        }
    except requests.exceptions.RequestException as error:
        print(f"Ошибка при загрузке расписания из сети: {error}")

    cached_data = _get_cached_schedule(week_id, entity_info)
    if cached_data:
        return (
            cached_data["schedule"],
            cached_data["days_list"],
            cached_data["prev_week_id"],
            cached_data["next_week_id"],
            {
                "source": "cache",
                "cache_updated_at": cached_data["updated_at"],
                "message": "Нет соединения с сайтом расписания. Показана сохранённая локальная версия.",
            },
        )

    return {}, [], None, None, {
        "source": "none",
        "cache_updated_at": None,
        "message": "Не удалось загрузить расписание из интернета и локальный кэш отсутствует.",
    }
