# APKLife Native (Variant B: Offline Flask-in-APK)

Этот вариант запускает Flask **локально внутри APK** через Chaquopy и открывает WebView на `http://127.0.0.1:5000`.

## Что нужно

- Android Studio (JDK 17)
- Android SDK + build-tools
- Интернет для загрузки Gradle/Chaquopy зависимостей

## Сборка debug APK

```bash
cd android_native
./gradlew :app:assembleDebug
```

Windows:

```bat
cd android_native
gradlew.bat :app:assembleDebug
```

## Где лежит APK

- `android_native/app/build/outputs/apk/debug/app-debug.apk`

## Как это работает

1. Kotlin `MainActivity` поднимает Python runtime (Chaquopy).
2. Вызывает `android_entry.start_server()`.
3. Flask стартует в background thread на `127.0.0.1:5000`.
4. После проверки порта WebView загружает локальный URL.

## Ограничения

- Первый build может идти долго из-за загрузки зависимостей.
- При изменении Python-кода он копируется задачей `syncPythonApp` перед сборкой.
