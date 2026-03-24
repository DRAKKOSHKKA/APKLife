"""Simple project i18n utilities without external dependencies."""

from __future__ import annotations

from flask import g, has_request_context, request

DEFAULT_LANG = "ru"
SUPPORTED_LANGS = ("ru", "en")

TRANSLATIONS: dict[str, dict[str, str]] = {
    "ru": {
        "app_title": "Расписание APKLife",
        "offline_indicator": "Нет сети. Показаны локальные данные.",
        "about_project": "О проекте",
        "about_text": "APKLife — локальное веб-приложение с офлайн-кэшем для студентов.",
        "technologies": "Технологии",
        "settings": "Настройки",
        "dark_theme": "Тёмная тема",
        "dev_mode": "DEV режим",
        "refresh_schedule": "Обновить расписание",
        "reset_group": "Сбросить выбранную группу",
        "close": "Закрыть",
        "info": "Инфо",
        "search_hint": "Введите группу, преподавателя или аудиторию",
        "search_placeholder": "11 нмо, Климова Т.С., актовый зал",
        "find_schedule": "Найти расписание",
        "schedule": "Расписание",
        "last_update": "Последнее обновление",
        "no_lesson": "Нет пары",
        "rest_time": "Можно отдохнуть",
        "back": "Назад",
        "group_required": "Не указано название группы",
        "group_not_found": "'{name}' не найдено",
        "invalid_group_params": "Некорректные параметры группы.",
        "shown_cached": "Показана сохранённая локальная версия.",
        "loaded_network": "Актуальные данные загружены из интернета.",
        "no_data_no_cache": "Не удалось получить расписание и кэш отсутствует.",
        "warning_source_changed": (
            "Источник недоступен или изменил структуру. " "Показаны данные из кэша."
        ),
        "data_missing": "Данные для загрузки не указаны.",
        "unexpected_error": "Произошла непредвиденная ошибка.",
        "language": "Язык",
        "lang_ru": "Русский",
        "lang_en": "English",
    },
    "en": {
        "app_title": "APKLife Schedule",
        "offline_indicator": "No network. Showing local cached data.",
        "about_project": "About",
        "about_text": "APKLife is a local web app with offline cache for students.",
        "technologies": "Technologies",
        "settings": "Settings",
        "dark_theme": "Dark theme",
        "dev_mode": "DEV mode",
        "refresh_schedule": "Refresh schedule",
        "reset_group": "Reset selected group",
        "close": "Close",
        "info": "Info",
        "search_hint": "Enter group, teacher, or classroom",
        "search_placeholder": "11 nmo, Klimova T.S., assembly hall",
        "find_schedule": "Find schedule",
        "schedule": "Schedule",
        "last_update": "Last update",
        "no_lesson": "No lesson",
        "rest_time": "Take a rest",
        "back": "Back",
        "group_required": "Group name is required",
        "group_not_found": "'{name}' not found",
        "invalid_group_params": "Invalid group parameters.",
        "shown_cached": "Showing saved local version.",
        "loaded_network": "Latest data loaded from the network.",
        "no_data_no_cache": "Unable to load schedule and cache is missing.",
        "warning_source_changed": "Source is unavailable or changed schema. Showing cached data.",
        "data_missing": "Load parameters are missing.",
        "unexpected_error": "An unexpected error occurred.",
        "language": "Language",
        "lang_ru": "Русский",
        "lang_en": "English",
    },
}


def resolve_lang() -> str:
    """Resolve active language from query, cookie or Accept-Language."""
    if not has_request_context():
        return DEFAULT_LANG

    query_lang = (request.args.get("lang") or "").strip().lower()
    if query_lang in SUPPORTED_LANGS:
        g.lang = query_lang
        return query_lang

    cookie_lang = (request.cookies.get("lang") or "").strip().lower()
    if cookie_lang in SUPPORTED_LANGS:
        g.lang = cookie_lang
        return cookie_lang

    header = (request.headers.get("Accept-Language") or "").lower()
    if header:
        for part in header.split(","):
            candidate = part.split(";")[0].strip().split("-")[0]
            if candidate in SUPPORTED_LANGS:
                g.lang = candidate
                return candidate

    g.lang = DEFAULT_LANG
    return DEFAULT_LANG


def current_lang() -> str:
    if has_request_context() and getattr(g, "lang", None) in SUPPORTED_LANGS:
        return str(g.lang)
    return DEFAULT_LANG


def tr(key: str, **kwargs: object) -> str:
    lang = current_lang()
    template = TRANSLATIONS.get(lang, TRANSLATIONS[DEFAULT_LANG]).get(key, key)
    return template.format(**kwargs) if kwargs else template
