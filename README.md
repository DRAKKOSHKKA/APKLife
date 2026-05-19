# APKLife Android

📱 Нативная Android-обёртка для расписания APKLife.

**Подробная документация:** [README.ru.md](README.ru.md)

## Быстрый старт

1. Откройте `android_native/` в Android Studio
2. Дождитесь синхронизации Gradle
3. Build → Build APK(s)

## Архитектура

Flask-сервер запускается локально внутри APK через Chaquopy (Python 3.10).
WebView отображает интерфейс с `http://127.0.0.1:5000`.
