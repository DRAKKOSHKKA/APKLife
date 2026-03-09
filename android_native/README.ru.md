# APKLife Native (Вариант B: Offline Flask-in-APK) — RU

Этот вариант запускает Flask **внутри APK** (Chaquopy) и открывает WebView на `http://127.0.0.1:5000`.

## Требования
- Android Studio
- JDK 17
- Android SDK + build tools
- Интернет для первой загрузки зависимостей Gradle/Chaquopy

## Сборка debug APK
### Linux/macOS
```bash
cd android_native
./gradlew :app:assembleDebug
```

### Windows (CMD/PowerShell)
```bat
cd android_native
gradlew.bat :app:assembleDebug
```

## Где лежит APK
- `android_native/app/build/outputs/apk/debug/app-debug.apk`

## Логика запуска
1. `MainActivity` запускает Python runtime Chaquopy.
2. Вызывает `android_entry.start_server()`.
3. Flask стартует в background thread на `127.0.0.1:5000`.
4. После проверки готовности WebView открывает локальный URL.

## Примечания
- Первая сборка может быть долгой из-за загрузки зависимостей.
- Python-файлы синхронизируются задачей Gradle перед сборкой.

Назад: [../README.ru.md](../README.ru.md)
