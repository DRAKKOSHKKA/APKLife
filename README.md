# APKLife

APKLife is a Flask-based student schedule application with cache-first loading, offline fallback, parser hardening, PWA support, and Android build options.

## Architecture overview
- **Presentation:** Flask routes in `routes/`
- **Service orchestration:** `services/schedule.py`, `services/utils_schedule.py`
- **Source integration:** `services/http_client.py`, `services/schedule_parser.py`, `services/sources/`
- **Persistence:** `services/cache_store.py`
- **Diagnostics:** metrics, structured logs, `/health`

See full rules in `docs/ARCHITECTURE.md`.

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
make install
make run
```

## Environment configuration
Copy `.env.example` and override values via environment variables.
Key options:
- `APP_HOST`, `APP_PORT`, `APP_DEBUG`
- `REQUEST_TIMEOUT_SECONDS`
- `CACHE_FILE`, `FAILED_HTML_DIR`

## Testing
```bash
make test
```

## Linting and formatting
```bash
make lint
```
This runs ruff, black check, and mypy.

## Troubleshooting
- If schedule source structure changed, snapshots are saved in `data/failed_html/`.
- If source is unavailable, app serves the last valid cache and returns warning metadata.
- Check logs in `logs/app.log`.

## Android build: Variant A (Capacitor wrapper)
Fast WebView shell pointing to remote `base_url`.

```bash
python bridge.py --base-url https://example.com --debug
python bridge.py --base-url https://example.com --release
python bridge.py --base-url https://example.com --release --aab
python bridge.py --base-url https://example.com --clean
```
Expected output paths:
- Debug APK: `android_bridge/android/app/build/outputs/apk/debug/app-debug.apk`
- Release APK: `android_bridge/android/app/build/outputs/apk/release/app-release.apk`
- Release AAB: `android_bridge/android/app/build/outputs/bundle/release/app-release.aab`

## Android build: Variant B (Flask inside APK)
See `android_native/README.md` for Chaquopy-based offline variant.
