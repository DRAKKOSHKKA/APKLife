# 📘 APK Life

**APK Life** — локальное веб-приложение для студентов и преподавателей **АПК Альметьевск**.

## ✨ Возможности

- Cache-first расписание с локальным кэшем и офлайн-фолбэком.
- Быстрый поиск по группе/преподавателю/аудитории.
- PWA (manifest + service worker).
- DEV-режим с метриками и логами.

## ▶️ Запуск веб-версии

```bash
pip install flask requests beautifulsoup4
python app.py
```

## ✅ Тесты парсера

```bash
python -m unittest discover -s tests -p "test_*.py"
```

---

## Android build: Variant A (Capacitor wrapper)

Это быстрый shell-APK: WebView открывает URL (`--base-url`).

### Требования

- Node.js (npm/npx)
- Java 17+
- Android SDK (`ANDROID_HOME` или `ANDROID_SDK_ROOT`)
- Git (опционально, для `--pull`)

### Команды

```bash
python bridge.py --debug --base-url https://example.com
python bridge.py --release --base-url https://example.com
python bridge.py --release --aab --clean --base-url https://example.com
```

### Что исправлено в bridge.py

- Идемпотентный init Capacitor:
  - `cap init` запускается, только если нет `capacitor.config.json/.ts`.
- Идемпотентный add/sync платформы:
  - `cap add android` только если нет `android_bridge/android`, иначе `cap sync android`.
- Windows-совместимость:
  - автоматический поиск `npm.cmd`/`npx.cmd`/`git`.
  - корректный wrapper `gradlew.bat` на Windows.
- Поддержка флагов:
  - `--debug` / `--release` (по умолчанию debug)
  - `--aab` (только с `--release`)
  - `--clean`
- В конце печатаются **абсолютные пути** собранных артефактов (APK/AAB).

### Ожидаемые output paths

- Debug APK: `android_bridge/android/app/build/outputs/apk/debug/app-debug.apk`
- Release APK: `android_bridge/android/app/build/outputs/apk/release/app-release.apk`
- Release AAB: `android_bridge/android/app/build/outputs/bundle/release/app-release.aab`

---

## Android build: Variant B (Offline Flask-in-APK)

Это “настоящий локальный бэкенд”: Flask запускается **внутри APK** (Chaquopy), WebView открывает `http://127.0.0.1:5000`.

См. подробности: `android_native/README.md`.

Быстрый старт:

```bash
cd android_native
./gradlew :app:assembleDebug
```

Windows:

```bat
cd android_native
gradlew.bat :app:assembleDebug
```

APK:
- `android_native/app/build/outputs/apk/debug/app-debug.apk`
