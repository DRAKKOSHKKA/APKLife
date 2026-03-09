# APKLife (Русский)

APKLife — это Flask-приложение для студентов с:

* cache-first загрузкой,
* офлайн-фолбэком,
* устойчивым HTML-парсером,
* опциональной проверкой обновлений через GitHub,
* поддержкой PWA,
* Android-вариантами сборки.

## Карта документации

* [Архитектура](architecture.ru.md)
* [Гайд для контрибьюторов](contributing.ru.md)
* [Кодекс поведения](code_of_conduct.ru.md)
* [Android Native (Variant B)](readme.ru-1.md)

## Быстрый старт

### Linux/macOS

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
make run
```

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
make run
```

### Windows (CMD)

```bat
python -m venv .venv
.\.venv\Scripts\activate.bat
pip install -r requirements-dev.txt
make run
```

Адрес приложения: `http://127.0.0.1:5000`

## Основные команды

```bash
make test
make lint
```

## Переменные окружения

Используйте `.env.example` как шаблон.

Ключевые настройки:

* Приложение: `APP_HOST`, `APP_PORT`, `APP_DEBUG`
* Таймауты HTTP: `CONNECT_TIMEOUT_SECONDS`, `READ_TIMEOUT_SECONDS`
* Кэш и диагностика: `CACHE_FILE`, `FAILED_HTML_DIR`, `LOGS_DIR`
* Опциональные GitHub-проверки: `GITHUB_TOKEN`, `GITHUB_API_USER_AGENT`, `GITHUB_CONNECT_TIMEOUT_SECONDS`, `GITHUB_READ_TIMEOUT_SECONDS`

## Опциональный GitHub-токен (не обязателен)

Проверка обновлений GitHub работает в режиме **best-effort** и без токена.

Если нужен более высокий лимит GitHub API, задайте свой PAT локально:

```bash
export GITHUB_TOKEN=your_personal_token
```

Windows (PowerShell):

```powershell
$env:GITHUB_TOKEN="your_personal_token"
```

Безопасность:

* Не коммитьте секреты.
* `.env` исключён из git.

## Сборка Android

### Вариант A: Capacitor wrapper

```bash
python bridge.py --base-url https://example.com --debug
python bridge.py --base-url https://example.com --release
python bridge.py --base-url https://example.com --release --aab
```

Артефакты:

* `android_bridge/android/app/build/outputs/apk/debug/app-debug.apk`
* `android_bridge/android/app/build/outputs/apk/release/app-release.apk`
* `android_bridge/android/app/build/outputs/bundle/release/app-release.aab`

### Вариант B: Offline Flask-in-APK

См.: [README.md](readme.ru-1.md)

## Диагностика

* Снимки HTML при проблемах схемы: `data/failed_html/`
* Логи приложения: `logs/app.log`
* Health endpoint: `/health`

[Назад к переключателю языка](../)
