# 📘 APK Life

**APK Life** — локальное веб-приложение для студентов и преподавателей **АПК Альметьевск**.
Оно работает на телефонах, планшетах и ПК, сохраняет расписание локально и умеет переключаться на офлайн-кэш.

## ✨ Основные возможности

- 📅 Просмотр расписания по группе, преподавателю и аудитории.
- 💾 Локальный кэш расписания в файл на устройстве.
- 🌐 Автопереключение на кэш, если сайт недоступен или отвечает дольше 15 секунд.
- ⚡ Cache-first загрузка: сначала показывается локальная версия, затем выполняется фоновое обновление.
- 📶 Офлайн-индикатор состояния сети и отображение состояния кэша.
- 🕒 Отображение времени последнего успешного обновления расписания.
- 🔄 Проверка версии приложения и release-метки относительно GitHub.
- 🧪 Автотесты парсера расписания (unittest).
- 🖤 Тёмная тема, быстрый поиск и адаптивный интерфейс под разные экраны.
- 📱 PWA режим (manifest + service worker) и Android bridge-сборка APK через `bridge.py`.
- 🛠️ DEV режим (10 нажатий по служебной метке в инфо-модалке): подробные метрики, кэш/сеть и логи.

## 🧩 Архитектура

- `services/utils_schedule.py` — orchestration загрузки, cache-first/fallback, интернет-проверка.
- `services/schedule_parser.py` — разбор HTML расписания и выделение уроков.
- `services/validators.py` — валидация и нормализация входных/кэш-данных.
- `services/cache_store.py` — чтение/запись локального кэша расписания + история изменений.
- `services/metrics.py` — in-memory метрики состояния сети/кэша/загрузок.
- `services/version.py` — проверка локальной/удалённой версии и latest release.
- `services/logger.py` — единая конфигурация подробного логирования (console + `logs/app.log`).
- `bridge.py` — сборка Android APK-обёртки для запуска веб-приложения как мобильного приложения.

## 🚀 Технологии

- **Backend:** Python 3, Flask, Requests, BeautifulSoup4
- **Frontend:** HTML5, CSS3 (MD3-inspired), Bootstrap 5, Bootstrap Icons, Vanilla JavaScript
- **Хранение:** JSON-файлы (`static/suggestions.json`, `cache/schedule_cache.json`)
- **Интеграции:** API сайта расписания `it-institut.ru`, GitHub API для проверки обновлений
- **PWA:** `manifest.webmanifest`, `service worker`
- **Android bridge:** Capacitor Android (`@capacitor/core`, `@capacitor/android`)

## ▶️ Запуск веб-версии

```bash
pip install flask requests beautifulsoup4
python app.py
```

После запуска приложение будет доступно по адресу: `http://127.0.0.1:5000`.

## ✅ Тесты парсера

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## 📦 Сборка APK (bridge)

> Требуется: Node.js/npm, Java 17+, Android SDK (`ANDROID_HOME` или `ANDROID_SDK_ROOT`).

```bash
python bridge.py --pull          # debug APK
python bridge.py --pull --release
```

После успешной сборки скрипт выведет путь к готовому `.apk`.
