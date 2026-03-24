# Структура проекта APKLife (RU)

Этот файл объясняет, где находится каждая часть репозитория и за что она отвечает.

## Корень проекта
- `app.py` — точка входа Flask и сборка приложения.
- `config.py` — совместимость/мост для конфигурации.
- `bridge.py` — сборочный bridge для Android Variant A (Capacitor wrapper).
- `Makefile` — команды разработчика (`install`, `test`, `lint`, `run`).
- `pyproject.toml` — метаданные проекта и настройки инструментов.
- `requirements.txt` / `requirements-dev.txt` — runtime/dev зависимости.
- `.env.example` — шаблон переменных окружения.

## Основной backend
- `routes/`
  - `main.py` — index + health роуты.
  - `group.py` — страница расписания + refresh/metrics/logs API.
- `services/`
  - `config.py` — типизированные runtime-настройки.
  - `http_client.py` — HTTP-обёртка с retry/timeout и meta-fetch.
  - `schedule_parser.py` — парсер HTML расписания и schema-эвристики.
  - `utils_schedule.py` — cache-first оркестрация и fallback источника.
  - `schedule.py` — сборка контекста для роутов расписания.
  - `cache_store.py` — хранение кэша/истории.
  - `version.py` — опциональная best-effort проверка обновлений GitHub.
  - `i18n.py` — локализация UI/backend.
  - `metrics.py`, `runtime_state.py` — диагностика и runtime-статус.
  - `logging_config.py`, `logger.py` — структурированное логирование.
  - `validators.py`, `normalize.py` — нормализация и валидация данных.
  - `exceptions.py`, `types.py` — доменные ошибки и типовые контракты.
  - `sources/` — абстракция источника и HTML-адаптер.

## Frontend
- `templates/` — Jinja-шаблоны (base/index/group/errors/partials).
- `static/`
  - `style.css` — стили приложения.
  - `scripts.js` — клиентские взаимодействия, dev mode, SW registration.
  - `sw.js`, `manifest.webmanifest` — поддержка PWA.
  - `suggestions.json` — локальные данные автоподсказок.

## Мобильные обёртки
- `android_native/` — Variant B (Chaquopy, Flask внутри APK).
- `android_bridge/` — Variant A generated bridge assets (при локальной сборке).

## Тесты
- `tests/test_schedule_parser.py` — тесты устойчивости парсера.
- `tests/test_version.py` — тесты устойчивости проверки версии GitHub.
- `tests/fixtures/` — HTML-фикстуры для сценариев парсера.

## Документация
- `README*.md` — overview проекта по языкам.
- `CONTRIBUTING*.md` — правила контрибьюта по языкам.
- `CODE_OF_CONDUCT*.md` — правила сообщества по языкам.
- `docs/ARCHITECTURE*.md` — архитектурная документация по языкам.
- `docs/PROJECT_STRUCTURE*.md` — карта структуры проекта по языкам.
- `.github/*` — двуязычные шаблоны issue/PR.

Назад: [README.ru.md](../README.ru.md)
