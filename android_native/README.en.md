# APKLife Native (Variant B: Offline Flask-in-APK) — EN

This variant runs Flask **inside APK** (Chaquopy) and opens WebView on `http://127.0.0.1:5000`.

## Requirements
- Android Studio
- JDK 17
- Android SDK + build tools
- Internet access for initial Gradle/Chaquopy dependency download

## Build debug APK
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

## Output APK
- `android_native/app/build/outputs/apk/debug/app-debug.apk`

## Runtime flow
1. `MainActivity` starts Chaquopy Python runtime.
2. Calls `android_entry.start_server()`.
3. Flask runs in background thread on `127.0.0.1:5000`.
4. WebView loads local URL after readiness check.

## Notes
- First build can be slow due to dependency downloads.
- Python app files are synced before build by Gradle task.

Back: [../README.en.md](../README.en.md)
