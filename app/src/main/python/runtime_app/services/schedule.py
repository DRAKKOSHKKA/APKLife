"""
Модуль для построения контекста расписания для шаблонов UI и API-эндпоинтов.

Этот модуль отвечает за подготовку и форматирование данных, которые передаются
в HTML-шаблоны или возвращаются в формате JSON при асинхронных запросах.
Он координирует работу с кэшем, проверку интернет-соединения и поиск информации о группах.
Подходит для Junior: здесь реализована простая и понятная логика построения контекста.
"""

from __future__ import annotations

import datetime
from datetime import timezone, timedelta
from typing import Any

from services.cache_store import build_cache_key, get_schedule_cache
from services.exceptions import ScheduleError
from services.i18n import tr
from services.metrics import snapshot
from services.runtime_state import mark_error, mark_success
from services.calls import WEEKDAY_SCHEDULE, SATURDAY_SCHEDULE
from services.utils_schedule import (
    cache_state_for,
    fetch_network_schedule,
    get_academic_week_number,
    get_cached_entity_info,
    get_current_week,
    get_group_info,
    get_schedule,
    internet_available,
)


def build_base_context() -> dict[str, Any]:
    """
    Создает базовый словарь контекста с дефолтными значениями.

    Зачем это нужно?
    В Flask и Jinja2 очень легко получить ошибку KeyError (когда шаблон пытается обратиться
    к переменной, которой нет в контексте). Чтобы этого не происходило, мы заранее объявляем
    все возможные переменные со значением None или пустыми структурами.
    Это гарантирует надежность рендеринга страниц.
    """
    return {
        "group_info": None,  # Метаданные выбранной группы (ID, имя, тип)
        "schedule": {},  # Расписание занятий по дням недели
        "days_list": [],  # Список доступных дней в текущей неделе
        "prev_week_id": None,  # ID предыдущей недели для пагинации
        "next_week_id": None,  # ID следующей недели для пагинации
        "active_day": None,  # Активный (выбранный) день для отображения
        "week_id": None,  # ID текущей недели
        "week_number_display": None,  # Отображаемый учебный номер недели (например, 19)
        "error": None,  # Описание возникшей ошибки (если есть)
        "corrected_name": None,  # Исправленное имя группы при автодополнении
        "no_lessons_week": True,  # Флаг: пустая ли неделя (нет ли вообще занятий)
        "schedule_source": None,  # Источник расписания: 'cache' или 'network'
        "schedule_message": None,  # Статусное сообщение для пользователя
        "cache_updated_at": None,  # Время последнего обновления кэша
        "offline": False,  # Флаг: находится ли приложение в оффлайне
        "cache_state": "missing",  # Статус кэша для DEV-панели ('hot' или 'empty')
        "cache_history": [],  # История кэширования группы для отладки
        "warning": None,  # Предупреждения (например, устаревший кэш при ошибке сети)
        "error_type": None,  # Тип технической ошибки для логов
        "metrics": {},  # Системные метрики для DEV-панели
    }


def detect_active_day(schedule: dict[str, Any], day_param: str | None) -> str | None:
    """
    Автоматически определяет активный день недели для отображения.

    Как работает алгоритм:
    1. Если пользователь явно передал день во входных параметрах (day_param), мы ищем
       день в расписании, который начинается с этой строки (например, "Вт").
    2. Если параметр не передан, мы берем сегодняшний системный день недели с помощью
       datetime.datetime.now().weekday() и преобразуем его в короткий русский формат ("Пн", "Вт").
    3. Если сегодняшний день есть в расписании, мы делаем его активным.
    4. Если сегодня воскресенье или дня нет в расписании, мы просто возвращаем первый доступный
       день из расписания (например, Понедельник).
    """
    if not schedule:
        return None

    # Шаг 1: Проверяем явный запрос дня от пользователя
    if day_param:
        for day in schedule.keys():
            if day.startswith(day_param):
                return day

    # Шаг 2: Вычисляем текущий день недели на сервере
    weekday = datetime.datetime.now().weekday()
    ru_days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    today = ru_days[weekday]

    # Шаг 3: Проверяем, есть ли сегодня занятия
    for day in schedule.keys():
        if day.startswith(today):
            return day

    # Шаг 4: Возвращаем первый день по умолчанию
    return next(iter(schedule))


def mark_current_lessons(schedule: dict[str, Any], active_day: str | None, test_time: str | None = None):
    """
    Помечает уроки, которые идут в данный момент (МСК).
    Поддерживает параметр test_time в формате 'ЧЧ:ММ' для отладки.
    """
    if not active_day or not schedule.get(active_day):
        return

    # MSK is UTC+3
    now_msk = datetime.datetime.now(timezone(timedelta(hours=3)))

    if test_time:
        try:
            h, m = map(int, test_time.split(":"))
            current_time_minutes = h * 60 + m
        except Exception:
            current_time_minutes = now_msk.hour * 60 + now_msk.minute
    else:
        current_time_minutes = now_msk.hour * 60 + now_msk.minute

    # Проверяем, совпадает ли активный день с сегодняшним (по МСК)
    weekday = now_msk.weekday()
    ru_days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    today_short = ru_days[weekday]

    # Если мы не в режиме тестирования, то подсвечиваем только сегодня
    if not test_time and not active_day.startswith(today_short):
        return

    is_sat = "Суббота" in active_day or "Сб" in active_day
    current_calls = SATURDAY_SCHEDULE if is_sat else WEEKDAY_SCHEDULE
    # Извлекаем только уроки
    lesson_calls = [c for c in current_calls if c[0] == 'lesson']

    for idx, lesson_list in enumerate(schedule[active_day]):
        # Получаем время для текущей пары по индексу
        if idx < len(lesson_calls):
            _, _, start, end = lesson_calls[idx]
            sh, sm = map(int, start.split(":"))
            eh, em = map(int, end.split(":"))
            start_m = sh * 60 + sm
            end_m = eh * 60 + em

            is_current_period = start_m <= current_time_minutes < end_m

            for lesson in lesson_list:
                if is_current_period:
                    lesson["is_current"] = True
                # Обновляем время в самом объекте урока, чтобы в шаблоне было проще
                lesson["time"] = f"{start}-{end}"


def _resolve_entity(group_name: str):
    """
    Вспомогательная функция для разрешения имени группы в метаданные.

    Сначала мы ищем подходящую группу в локальном кэше (Cache-first!).
    Это позволяет приложению открывать расписание МГНОВЕННО без ожидания сети.
    Если в кэше ничего нет, тогда идем в интернет через get_group_info.
    """
    # 1. Сначала проверяем локальный кэш
    cached_entity = get_cached_entity_info(group_name)
    if cached_entity:
        return cached_entity, cached_entity.get("SearchString")

    # 2. Только если в кэше пусто — идем в сеть (может занять время)
    entity_info, corrected_name = get_group_info(group_name)
    if entity_info:
        return entity_info, corrected_name

    return None, None


def _with_cache_state(context: dict[str, Any], week_id: int, entity_info: dict[str, object] | None):
    """
    Обогащает контекст данными о состоянии кэша для DEV-панели.

    Показывает Junior-разработчикам и администраторам, загружено ли расписание из горячего кэша
    и выводит историю последних обновлений (до 5 последних записей).
    """
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
    """
    Основная функция загрузки контекста расписания (Cache-first стратегия).

    Этот метод используется при обычном посещении страницы группы:
    1. Парсит входные параметры (имя группы, ID недели, день).
    2. Разрешает группу в метаданные.
    3. Запрашивает расписание: сначала из локального кэша, и только если кэша нет — идет в сеть.
    4. Фильтрует расписание под один активный день (если день выбран).
    5. Заполняет контекст метриками и оффлайн-статусом.
    """
    context = build_base_context()

    group_name = (args.get("group_name") or "").strip()
    week_id = args.get("week_id", type=int)
    day = args.get("day")

    active_week_id = week_id or get_current_week()
    context["week_id"] = active_week_id
    context["week_number_display"] = get_academic_week_number(active_week_id)

    # Проверяем обязательность имени группы
    if not group_name:
        context["error"] = tr("group_required")
        return context

    # Разрешаем группу в метаданные
    entity_info, corrected_name = _resolve_entity(group_name)
    if not entity_info:
        context["error"] = tr("group_not_found", name=group_name)
        return context

    # Запрашиваем расписание по Cache-first стратегии
    force_refresh = args.get("force_refresh") == "1"
    schedule, days_list, prev_week, next_week, source_meta = get_schedule(
        week_id or get_current_week(),
        entity_info,
        prefer_cache=not force_refresh,
    )

    # Определяем активный день и оставляем в расписании только его (для чистой верстки)
    active_day = detect_active_day(schedule, day)

    # Помечаем текущие уроки (Feature: Lesson Highlighting)
    mark_current_lessons(schedule, active_day, args.get("test_time"))

    if active_day:
        schedule = {active_day: schedule[active_day]}

    # Заполняем контекст результатами
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
            "offline": source_meta.get("source") == "cache", # Отключена активная проверка интернета при загрузке кэша
            "warning": source_meta.get("warning"),
            "error_type": source_meta.get("error_type"),
            "metrics": snapshot(),
            "test_time": args.get("test_time"),
        }
    )
    context = _with_cache_state(context, week_id or get_current_week(), entity_info)

    # Логируем успешность выполнения операции для метрик рантайма
    if not schedule:
        context["error"] = source_meta.get("message")
        mark_error(str(source_meta.get("message")))
    else:
        mark_success()
    return context


def force_refresh_context(args):
    """
    Принудительное обновление контекста расписания из сети (Network-only стратегия).

    Вызывается при клике на кнопку 'Обновить расписание' или при фоновом обновлении:
    1. Игнорирует кэш и напрямую запрашивает свежие данные с сайта колледжа.
    2. В случае успеха — обновляет локальный кэш.
    3. Если сеть лежит — плавно откатывается на имеющийся кэш, сообщая пользователю предупреждение.
    """
    group_name = (args.get("group_name") or "").strip()
    week_id = args.get("week_id", type=int) or get_current_week()

    if not group_name:
        return build_base_context() | {"error": tr("group_required")}

    entity_info, corrected_name = _resolve_entity(group_name)
    if not entity_info:
        return build_base_context() | {"error": tr("group_not_found", name=group_name)}

    try:
        # Пытаемся получить свежие данные напрямую из сети
        schedule, days_list, prev_week, next_week, source_meta = fetch_network_schedule(
            week_id, entity_info
        )
    except ScheduleError:
        # Сеть лежит — плавно откатываемся на кэш
        schedule, days_list, prev_week, next_week, source_meta = get_schedule(
            week_id, entity_info, prefer_cache=True
        )

    active_day = detect_active_day(schedule, args.get("day"))

    # Помечаем текущие уроки (Feature: Lesson Highlighting)
    mark_current_lessons(schedule, active_day, args.get("test_time"))

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
            "week_number_display": get_academic_week_number(week_id),
            "schedule_source": source_meta.get("source"),
            "schedule_message": source_meta.get("message"),
            "cache_updated_at": source_meta.get("cache_updated_at"),
            "warning": source_meta.get("warning"),
            "error_type": source_meta.get("error_type"),
            "error": source_meta.get("message") if not schedule else None,
            "offline": False, # Не проверяем сеть при загрузке из кэша
            "metrics": snapshot(),
            "test_time": args.get("test_time"),
        }
    )
    context = _with_cache_state(context, week_id, entity_info)
    if schedule:
        mark_success()
    else:
        mark_error(str(context.get("error")))
    return context
