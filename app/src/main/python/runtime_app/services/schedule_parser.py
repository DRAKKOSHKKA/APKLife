"""
HTML-парсер для страниц расписания с защитными проверками схемы и отказоустойчивым разбором.

Этот модуль отвечает за чтение сырой HTML-разметки, получаемой от сайта колледжа,
и преобразование ее в структурированный словарь Python (JSON-совместимый).
Специально для Junior: код снабжен подробнейшими комментариями на русском языке.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime

from bs4 import BeautifulSoup, Tag

from services.config import settings
from services.exceptions import ScheduleParseError, ScheduleSchemaChangedError
from services.logging_config import get_logger
from services.normalize import normalize_optional, normalize_text
from services.types import Lesson, ScheduleResult

# Настраиваем логирование, чтобы Junior мог видеть подробный рантайм-отчет при возникновении ошибок
logger = get_logger(__name__)

# Дефолтный объект "пустого" урока. Позволяет избежать ошибок KeyError в HTML-шаблонах
EMPTY_LESSON: Lesson = {
    "time": None,
    "subject": None,
    "teacher": None,
    "room": None,
    "group": None,
}

# Регулярные выражения (RegEx) для поиска и валидации временных диапазонов, дней недели и дат
_TIME_RANGE_RE = re.compile(
    r"(?:^|\b)(\d{1,2})[:.]?(\d{2})\s*[-–—]\s*(\d{1,2})[:.]?(\d{2})(?:$|\b)"
)
_WEEKDAY_RE = re.compile(
    r"\b(пн|вт|ср|чт|пт|сб|вс|понедельник|вторник|среда|четверг|пятница|суббота|воскресенье|"
    r"mon|tue|wed|thu|fri|sat|sun|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
    flags=re.IGNORECASE,
)
_DATE_RE = re.compile(r"\b\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?\b")


class SchemaDiagnostics(dict):
    """
    Класс-контейнер для диагностических данных схемы.
    Используется для сбора технической информации о структуре HTML-таблицы.
    """


def _save_failed_html(raw_html: str, reason: str, details: dict[str, object] | None = None) -> None:
    """
    Сохраняет сломанный HTML-код в локальный файл для последующего расследования разработчиками.

    Junior-совет:
    В продакшене структура внешнего сайта колледжа может внезапно измениться. Чтобы не гадать,
    почему упал парсер, эта функция сохраняет точную копию HTML-страницы и логгирует её хэш.
    """
    settings.failed_html_dir.mkdir(parents=True, exist_ok=True)
    html_hash = hashlib.sha256(raw_html.encode("utf-8", errors="ignore")).hexdigest()[:16]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = settings.failed_html_dir / f"{timestamp}_{html_hash}.html"
    path.write_text(raw_html, encoding="utf-8", errors="ignore")
    logger.error(
        "schema_guard_failed reason=%s hash=%s path=%s details=%s",
        reason,
        html_hash,
        path,
        details or {},
    )


def _cell_text(cell: Tag) -> str | None:
    """
    Извлекает очищенный текст из HTML-ячейки.
    Удаляет лишние пробелы и неразрывные пробелы (nbsp).
    """
    text = cell.get_text(" ", strip=True).replace("\xa0", " ")
    return normalize_optional(text)


def _normalize_header(text: str | None) -> str:
    """
    Нормализует текст заголовка для последующего надежного сравнения.
    Приводит текст к нижнему регистру.
    """
    return normalize_text((text or "").replace("\xa0", " "), lower=True) or ""


def _looks_like_time_header(value: str | None) -> bool:
    """
    Проверяет с помощью регулярного выражения, похож ли заголовок столбца на время пары.
    Пример корректного формата: '08:00-09:20'.
    """
    if not value:
        return False
    return bool(_TIME_RANGE_RE.search(value.replace(" ", "")) or _TIME_RANGE_RE.search(value))


def _looks_like_day_marker(value: str | None) -> bool:
    """
    Проверяет, похожа ли ячейка первого столбца на день недели или дату.
    Примеры: 'Понедельник' или '19.05'.
    """
    if not value:
        return False
    normalized = _normalize_header(value)
    return bool(_WEEKDAY_RE.search(normalized) or _DATE_RE.search(normalized))


def _find_schedule_table(soup: BeautifulSoup) -> Tag | None:
    """
    Находит главную таблицу расписания на странице.

    Алгоритм:
    Ищет все теги <table> в документе и выбирает ту таблицу, у которой наибольшее количество
    строк <tr>. Это очень надежный эвристический подход, страхующий от рекламных
    или сервисных табличек.
    """
    tables = soup.find_all("table")
    if not tables:
        return None
    return max(tables, key=lambda t: len(t.find_all("tr")))


def _extract_header_cells(table: Tag) -> list[Tag]:
    """Извлекает ячейки заголовка таблицы (сначала ищет тег thead, затем первую строку tr)."""
    thead = table.find("thead")
    if thead:
        header_row = thead.find("tr")
        if header_row:
            cells = header_row.find_all(["th", "td"], recursive=False)
            if cells:
                return cells
    first_row = table.find("tr")
    if first_row:
        return first_row.find_all(["th", "td"], recursive=False)
    return []


def _extract_body_rows(table: Tag) -> list[Tag]:
    """Извлекает только строки с контентом расписания (пропуская заголовок таблицы)."""
    tbody = table.find("tbody")
    if tbody:
        rows = tbody.find_all("tr", recursive=False)
        if rows:
            return rows
    rows = table.find_all("tr")
    if len(rows) > 1:
        return rows[1:]
    return []


def _expand_header_cells(header_cells: list[Tag]) -> list[str | None]:
    """
    Учитывает HTML-атрибут 'colspan' для ячеек заголовков.

    Junior-совет:
    Если ячейка заголовка имеет colspan="2", это означает, что она растягивается на 2 колонки.
    Мы должны продублировать ее имя в списке заголовков, чтобы индексы колонок
    совпадали со строками!
    """
    expanded: list[str | None] = []
    for cell in header_cells:
        text = _cell_text(cell)
        colspan_raw = cell.get("colspan", 1)
        try:
            colspan = max(int(colspan_raw), 1)
        except (TypeError, ValueError):
            colspan = 1
        expanded.extend([text] * colspan)
    return expanded


def _collect_diagnostics(
    table: Tag, header_cells: list[Tag], body_rows: list[Tag]
) -> SchemaDiagnostics:
    """Собирает техническую информацию о таблице для проверки соответствия структуры."""
    headers_raw = [_cell_text(cell) for cell in header_cells]
    headers_normalized = [_normalize_header(value) for value in headers_raw]
    expanded_headers = _expand_header_cells(header_cells)
    column_count = len(expanded_headers)

    first_column_values: list[str | None] = []
    for row in body_rows[:10]:
        cells = row.find_all(["th", "td"], recursive=False)
        first_column_values.append(_cell_text(cells[0]) if cells else None)

    time_like_count = sum(1 for value in expanded_headers[1:] if _looks_like_time_header(value))
    day_like_count = sum(1 for value in first_column_values if _looks_like_day_marker(value))

    diag: SchemaDiagnostics = SchemaDiagnostics(
        {
            "headers_raw": headers_raw,
            "headers_normalized": headers_normalized,
            "first_header_raw": headers_raw[0] if headers_raw else None,
            "first_header_normalized": headers_normalized[0] if headers_normalized else None,
            "row_count": len(body_rows),
            "column_count": column_count,
            "time_like_header_count": time_like_count,
            "day_like_row_count": day_like_count,
        }
    )
    return diag


def _validate_schedule_like_structure(
    table: Tag, body_rows: list[Tag], diag: SchemaDiagnostics
) -> tuple[bool, str]:
    """
    Защитный барьер схемы (Schema Guard).

    Перед тем как парсить данные, мы проверяем структуру таблицы:
    - Есть ли строки?
    - Достаточно ли колонок (минимум 2: день недели + занятия)?
    - Похожи ли ячейки на время и даты?
    Если проверки провалены — выкидываем ошибку изменения схемы, сохраняя HTML для анализа.
    """
    if not body_rows:
        return False, "empty_body"

    column_count = int(diag.get("column_count", 0) or 0)
    if column_count < 2:
        return False, "insufficient_columns"

    time_like_headers = int(diag.get("time_like_header_count", 0) or 0)
    day_like_rows = int(diag.get("day_like_row_count", 0) or 0)
    row_count = int(diag.get("row_count", 0) or 0)

    # Строгий режим: должны быть заголовки времени и маркеры дней
    if time_like_headers >= 1 and day_like_rows >= 1:
        return True, "strict_ok"

    # Отказоустойчивый (tolerant) режим: разрешаем парсить, если это явно таблица расписания
    if (
        row_count >= 1
        and day_like_rows >= 1
        and column_count >= 2
        and (time_like_headers >= 1 or (column_count >= 3 and row_count >= 2))
    ):
        return True, "tolerant_ok"

    return False, "unexpected_header_structure"


def _time_to_minutes(time_str: str) -> int:
    """Вспомогательный метод: переводит время формата 'ЧЧ:ММ' в количество минут от начала дня."""
    cleaned = time_str.strip().replace(".", ":")
    hours, minutes = map(int, cleaned.split(":"))
    return hours * 60 + minutes


def _minutes_to_time(minutes: int) -> str:
    """Вспомогательный метод: переводит минуты от начала дня обратно в строку 'ЧЧ:ММ'."""
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"


def split_time_interval(time_range: str | None, num_parts: int) -> list[str | None]:
    """
    Разбивает общий временной диапазон (например, спаренной пары) на равные отрезки.

    Зачем это нужно:
    Если в одной HTML-ячейке выведено два занятия подряд (спаренные пары),
    мы делим общее время пары (например, 08:00 - 11:10) на равные части,
    чтобы у каждого занятия было свое точное расписание!
    """
    if not time_range or num_parts <= 0:
        return [time_range] * max(num_parts, 1)

    normalized_range = (
        time_range.replace("–", "-").replace("—", "-").replace("−", "-").replace(".", ":")
    )
    if "-" not in normalized_range:
        return [time_range] * max(num_parts, 1)

    try:
        start_time, end_time = normalized_range.split("-", maxsplit=1)
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


def _parse_lesson_div(div: Tag, lesson_time: str | None) -> Lesson:
    """
    Парсит один HTML-блок занятия (обычно тег div или p).

    Извлекает название предмета, имя преподавателя, номер кабинета и группу.
    Мягко обрабатывает запятые и разделения в строках.
    """
    spans = [
        normalize_optional(span.get_text(" ", strip=True).replace("\xa0", " "))
        for span in div.find_all("span")
    ]
    if not spans:
        text = normalize_optional(div.get_text(" ", strip=True).replace("\xa0", " "))
        return {
            "time": normalize_optional(lesson_time),
            "subject": text,
            "teacher": None,
            "room": None,
            "group": None,
        }

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


def _parse_cell_lessons(cell: Tag, time_range: str | None) -> list[Lesson]:
    """
    Парсит содержимое ячейки таблицы.
    Ячейка может содержать как одно, так и несколько занятий.
    """
    lesson_blocks = cell.find_all(["div", "p"], recursive=False)
    if not lesson_blocks:
        nested = cell.find_all("div")
        lesson_blocks = nested if nested else []

    if lesson_blocks:
        intervals = split_time_interval(time_range, len(lesson_blocks))
        lessons: list[Lesson] = []
        for idx, block in enumerate(lesson_blocks):
            lessons.append(
                _parse_lesson_div(block, intervals[idx] if idx < len(intervals) else time_range)
            )
        return lessons

    text = normalize_optional(cell.get_text(" ", strip=True).replace("\xa0", " "))
    if text:
        return [
            {
                "time": normalize_optional(time_range),
                "subject": text,
                "teacher": None,
                "room": None,
                "group": None,
            }
        ]

    return [{**EMPTY_LESSON, "time": normalize_optional(time_range)}]


def parse_schedule_html(html_text: str, week_id: int | None = None) -> ScheduleResult:
    """
    Основная точка входа: парсит HTML-страницу расписания и строит структурированную карту.

    Junior-архитектура:
    1. Инициализирует BeautifulSoup для парсинга HTML дерева.
    2. Находит целевую таблицу с наибольшим числом строк.
    3. Запускает проверку Schema Guard для гарантии отсутствия поломок разметки.
    4. Обходит строки (дни недели) и ячейки (пары).
    5. Вырезает пустые пары в конце учебного дня, чтобы сэкономить место на экране (Feature 5.1).
    6. Вычисляет ID соседних недель математически для стабильной навигации.
    """
    try:
        soup = BeautifulSoup(html_text, "html.parser")
        table = _find_schedule_table(soup)
        if not table:
            _save_failed_html(html_text, "missing_table_or_sections", {"table_found": False})
            raise ScheduleSchemaChangedError("Missing schedule-like table")

        header_cells = _extract_header_cells(table)
        body_rows = _extract_body_rows(table)
        diagnostics = _collect_diagnostics(table, header_cells, body_rows)

        # Выполняем валидацию структуры
        is_valid, mode = _validate_schedule_like_structure(table, body_rows, diagnostics)
        logger.info(
            "schema_guard_diagnostics mode=%s first_header_raw=%s first_header_normalized=%s "
            "headers=%s row_count=%s column_count=%s "
            "time_like_header_count=%s day_like_row_count=%s",
            mode,
            diagnostics.get("first_header_raw"),
            diagnostics.get("first_header_normalized"),
            diagnostics.get("headers_normalized"),
            diagnostics.get("row_count"),
            diagnostics.get("column_count"),
            diagnostics.get("time_like_header_count"),
            diagnostics.get("day_like_row_count"),
        )
        if not is_valid:
            _save_failed_html(html_text, mode, dict(diagnostics))
            raise ScheduleSchemaChangedError(f"Schema guard failed: {mode}")
        if mode == "tolerant_ok":
            logger.warning("schema_guard_tolerant_mode_used diagnostics=%s", dict(diagnostics))

        # Определяем временные слоты на основе заголовков и их colspan.
        # Это позволяет корректно обрабатывать объединение ячеек (colspan) в заголовке.
        time_slots = []
        for cell in header_cells[1:]:
            text = _cell_text(cell)
            try:
                colspan = max(int(cell.get("colspan", 1)), 1)
            except (TypeError, ValueError):
                colspan = 1
            time_slots.append({"time": normalize_optional(text), "colspan": colspan})

        schedule: dict[str, list[list[Lesson]]] = {}
        days_list: list[str] = []

        # Обходим строки таблицы (каждая строка — отдельный день недели)
        for row in body_rows:
            cells = row.find_all(["th", "td"], recursive=False)
            if len(cells) < 1:
                continue

            day_text = _cell_text(cells[0])
            if not day_text:
                continue

            day_key = day_text
            days_list.append(day_key)
            lessons_for_day: list[list[Lesson]] = []

            lesson_cells = cells[1:]

            # Сопоставляем индекс колонки с конкретной ячейкой в строке.
            # Мы создаем плоский список ячеек, где ячейка с colspan=N повторяется N раз.
            col_to_cell = []
            for cell in lesson_cells:
                try:
                    cspan = max(int(cell.get("colspan", 1)), 1)
                except (TypeError, ValueError):
                    cspan = 1
                col_to_cell.extend([cell] * cspan)

            current_col = 0
            for slot in time_slots:
                slot_lessons: list[Lesson] = []

                # Собираем все уникальные ячейки, которые попадают в диапазон колонок этого слота
                cells_in_slot = []
                for _ in range(slot["colspan"]):
                    if current_col < len(col_to_cell):
                        cell = col_to_cell[current_col]
                        # Проверяем, не добавили ли мы уже эту ячейку (если она с colspan > 1)
                        if not cells_in_slot or cells_in_slot[-1] is not cell:
                            cells_in_slot.append(cell)
                        current_col += 1

                # Парсим каждую ячейку и объединяем уроки
                for cell in cells_in_slot:
                    parsed = _parse_cell_lessons(cell, slot["time"])
                    for lesson in parsed:
                        if lesson.get("subject"):
                            # Если найден реальный предмет, удаляем пустые заглушки из текущего слота
                            slot_lessons = [l for l in slot_lessons if l.get("subject")]

                            # Дедупликация: не добавляем один и тот же урок дважды
                            is_duplicate = any(
                                l.get("subject") == lesson.get("subject")
                                and l.get("teacher") == lesson.get("teacher")
                                and l.get("room") == lesson.get("room")
                                for l in slot_lessons
                            )
                            if not is_duplicate:
                                slot_lessons.append(lesson)
                        elif not slot_lessons:
                            # Добавляем пустой урок только если в слоте еще нет реальных предметов
                            slot_lessons.append(lesson)

                # Если слот остался пустым — гарантируем наличие хотя бы одного "пустого" объекта
                if not slot_lessons:
                    slot_lessons = [{**EMPTY_LESSON, "time": slot["time"]}]

                lessons_for_day.append(slot_lessons)

            # Обрезка пустых пар в конце дня (Feature 5.1):
            # Удаляем пустые уроки с конца списка, пока не встретим реальный урок.
            while lessons_for_day and all(
                not lesson.get("subject") for lesson in lessons_for_day[-1]
            ):
                lessons_for_day.pop()

            # Если весь день полностью пустой (выходной) — оставляем ровно одну пустую карточку
            if not lessons_for_day:
                lessons_for_day = [[{**EMPTY_LESSON}]]

            schedule[day_key] = lessons_for_day

        if not schedule:
            _save_failed_html(html_text, "parsed_empty_schedule", dict(diagnostics))
            raise ScheduleSchemaChangedError("Parsed table but extracted empty schedule")

        # Навигация по неделям:
        # Используем надежный математический расчет на основе текущего week_id
        prev_week_id = None
        next_week_id = None

        if week_id is not None:
            prev_week_id = week_id - 1
            next_week_id = week_id + 1
        else:
            # Резервный способ парсинга ссылок, если week_id не передан
            links = soup.select('a[href*="WeekId="]')
            parsed_ids = []
            for link in links:
                href = link.get("href", "")
                match = re.search(r"WeekId=(\d+)", href)
                if match:
                    parsed_ids.append(int(match.group(1)))

            if len(parsed_ids) == 2:
                prev_week_id = parsed_ids[0]
                next_week_id = parsed_ids[1]
            elif parsed_ids:
                parsed_ids = sorted(list(set(parsed_ids)))
                active_guess = None
                for i in range(len(parsed_ids) - 1):
                    if parsed_ids[i + 1] - parsed_ids[i] == 2:
                        active_guess = parsed_ids[i] + 1
                        break
                if active_guess is not None:
                    prev_week_id = active_guess - 1
                    next_week_id = active_guess + 1
                else:
                    prev_week_id = parsed_ids[0]
                    next_week_id = parsed_ids[-1]

        return {
            "schedule": schedule,
            "days_list": days_list,
            "prev_week_id": prev_week_id,
            "next_week_id": next_week_id,
        }
    except ScheduleSchemaChangedError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("schedule_parse_failed")
        raise ScheduleParseError("Failed to parse schedule HTML") from exc
