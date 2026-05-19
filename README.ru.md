# 📱 APKLife — Android-версия (WebView + Chaquopy)

## Как это работает

Приложение упаковывает Flask-сервер расписания прямо внутрь APK-файла с помощью **Chaquopy** — плагина, который встраивает полноценный Python-интерпретатор в Android-приложение.

```
┌──────────────────────────────────────────────┐
│          Android APK (APKLife)                │
│                                              │
│  ┌──────────┐    ┌────────────────────────┐  │
│  │  Kotlin   │    │  Chaquopy (Python 3.10) │  │
│  │  WebView  │◄──►│  Flask-сервер          │  │
│  │           │    │  127.0.0.1:5000        │  │
│  └──────────┘    └────────────────────────┘  │
│       ▲                    ▲                 │
│       │                    │                 │
│  Пользователь       it-institut.ru API       │
└──────────────────────────────────────────────┘
```

### Порядок запуска:
1. **Splash-экран** → Material 3 индикатор загрузки
2. **Chaquopy** инициализирует Python 3.10 внутри APK
3. `android_entry.py` запускает Flask на `127.0.0.1:5000`
4. MainActivity ждёт привязки порта (TCP polling)
5. **WebView** загружает `http://127.0.0.1:5000`
6. Пользователь взаимодействует с расписанием как в браузере

---

## Требования для сборки

| Инструмент | Версия |
|---|---|
| **Android Studio** | Hedgehog 2023.1.1+ |
| **JDK** | 17+ |
| **Android SDK** | API 34 (compileSdk) |
| **Gradle** | 8.5+ (через wrapper) |
| **Интернет** | Для загрузки Chaquopy и pip-зависимостей |

> ⚠️ **Важно**: Chaquopy автоматически скачивает Python-пакеты (`flask`, `requests`, `beautifulsoup4`) при первой сборке. Это требует стабильного интернета.

---

## Сборка APK

### Способ 1: Android Studio (рекомендуется)

1. Откройте Android Studio
2. **File → Open** → выберите папку `android_native/`
3. Дождитесь синхронизации Gradle (может занять 3-5 минут в первый раз)
4. **Build → Build Bundle(s) / APK(s) → Build APK(s)**
5. APK будет в `app/build/outputs/apk/debug/app-debug.apk`

### Способ 2: Командная строка

```bash
cd android_native

# Debug-сборка (для тестирования)
./gradlew assembleDebug

# Release-сборка (для публикации)
./gradlew assembleRelease
```

APK файл после сборки:
- Debug: `app/build/outputs/apk/debug/app-debug.apk`
- Release: `app/build/outputs/apk/release/app-release.apk`

### Способ 3: Установка напрямую на устройство

```bash
# Собрать и сразу установить на подключённый телефон
./gradlew installDebug
```

---

## Особенности Android-версии

| Функция | Описание |
|---|---|
| 🔄 **Pull-to-refresh** | Потяните вниз для перезагрузки расписания |
| ◀️ **Back-навигация** | Кнопка «Назад» перемещает по истории WebView |
| 🎨 **Material Design 3** | Splash-экран, цветовая схема, индикаторы |
| 🔌 **Offline-first** | Flask кэширует расписание локально в APK |
| 🐍 **Встроенный Python** | Chaquopy запускает Flask без внешнего сервера |
| 📱 **Полная автономность** | Не нужен внешний хостинг — всё внутри APK |

---

## Структура проекта

```
android_native/
├── build.gradle.kts          # Корневой Gradle (версии плагинов)
├── settings.gradle.kts       # Настройки проекта
├── gradle.properties         # JVM и AndroidX параметры
└── app/
    ├── build.gradle.kts      # Модуль app: Chaquopy, зависимости, sync-задача
    ├── proguard-rules.pro    # Правила минификации для release
    └── src/main/
        ├── AndroidManifest.xml
        ├── java/ru/apklife/app/
        │   └── MainActivity.kt    # WebView + Chaquopy запуск Flask
        ├── python/
        │   └── android_entry.py   # Python entrypoint для Flask
        └── res/
            ├── layout/
            │   └── activity_main.xml  # SwipeRefresh + WebView + Splash + Error
            └── values/
                ├── colors.xml     # MD3 цветовая палитра
                ├── strings.xml    # Строки на русском
                └── themes.xml     # MD3 Light тема + Splash
```

---

## FAQ

**Q: Почему APK такой большой?**
A: Chaquopy включает в APK полноценный Python 3.10 + pip-пакеты (~50-80 MB). Это необходимо для автономной работы Flask.

**Q: Можно ли уменьшить размер?**
A: Уберите ненужные `abiFilters` в `build.gradle.kts`. Например, оставьте только `arm64-v8a` для современных устройств.

**Q: Нужен ли интернет для работы?**
A: Для первого получения расписания — да (данные с it-institut.ru). После этого расписание кэшируется и работает оффлайн.

**Q: На каких версиях Android работает?**
A: Android 7.0+ (API 24, minSdk).
