# 📘 APK Life

**APK Life** — это локальное веб-приложение для студентов и преподавателей **АПК Альметьевск**.
Оно работает на телефонах, планшетах и ПК, сохраняет расписание локально и умеет переключаться на офлайн-кэш.

## ✨ Основные возможности

- 📅 Просмотр расписания по группе, преподавателю и аудитории.
- 💾 Локальный кэш расписания в файл на устройстве.
- 🌐 Автопереключение на кэш, если сайт недоступен или отвечает дольше 30 секунд.
- 🕒 Отображение времени последнего успешного обновления расписания.
- 🔄 Проверка версии приложения относительно GitHub-репозитория.
- 🖤 Тёмная тема, быстрый поиск и адаптивный интерфейс под разные экраны.
- 📱 Android bridge-сборка APK через `bridge.py` (Capacitor shell).

## 🧩 Архитектура (обновлено)

- `services/utils_schedule.py` — публичные сервисные функции, orchestration загрузки и fallback.
- `services/schedule_parser.py` — разбор HTML расписания и выделение уроков.
- `services/validators.py` — валидация и нормализация входных/кэш-данных.
- `services/cache_store.py` — чтение/запись локального кэша расписания.
- `services/version.py` — проверка локальной/удалённой версии приложения.
- `bridge.py` — сборка Android APK-обёртки для запуска веб-приложения как мобильного приложения.

## 🚀 Технологии

- **Backend:** Python 3, Flask, Requests, BeautifulSoup4
- **Frontend:** HTML5, CSS3 (адаптивная вёрстка), Bootstrap 5, Bootstrap Icons, Vanilla JavaScript
- **Хранение:** JSON-файлы (`static/suggestions.json`, `cache/schedule_cache.json`)
- **Интеграции:** API сайта расписания `it-institut.ru`, GitHub API для проверки обновлений
- **Android bridge:** Capacitor Android (`@capacitor/core`, `@capacitor/android`)

## ▶️ Запуск веб-версии

```bash
pip install flask requests beautifulsoup4
python app.py
```

После запуска приложение будет доступно по адресу: `http://127.0.0.1:5000`.

## 📦 Сборка APK (bridge)

> Требуется: Node.js/npm, Java 17+, Android SDK (`ANDROID_HOME` или `ANDROID_SDK_ROOT`).

```bash
python bridge.py --pull          # debug APK
python bridge.py --pull --release
```

После успешной сборки скрипт выведет путь к готовому `.apk`.
