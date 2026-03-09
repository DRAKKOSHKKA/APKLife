# Архитектура APKLife (RU)

## Слоистый дизайн

1. **Presentation layer**: `routes/*`, `templates/*`, `static/*`
2. **Service layer**: `services/schedule.py`, `services/utils_schedule.py`, `services/version.py`
3. **Source layer**: `services/sources/*`, `services/http_client.py`, `services/schedule_parser.py`
4. **Cache layer**: `services/cache_store.py`
5. **Utility layer**: `services/normalize.py`, `services/validators.py`, `services/logging_config.py`

## Основные принципы

* Роуты валидируют вход и возвращают ответы.
* Роуты не должны делать прямые сетевые вызовы.
* Роуты не должны напрямую менять кэш.
* Логика внешнего источника должна быть изолирована через source/parser/http абстракции.

## Паттерны надёжности

* Типизированные доменные ошибки в `services/exceptions.py`.
* Retry + timeout в `services/http_client.py`.
* Парсинг с проверкой схемы, диагностикой и сохранением snapshot в `services/schedule_parser.py`.
* Cache-first поведение в `services/utils_schedule.py`.

## Наблюдаемость

* Структурированные логи через `services/logging_config.py`.
* Runtime-метрики через `services/metrics.py`.
* Health endpoint в `routes/main.py`.

## Точки расширения

* Новые провайдеры расписания могут реализовать интерфейс `services/sources/base.py`.
* Переводы UI управляются через `services/i18n.py`.
