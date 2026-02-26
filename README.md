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
pip install -r requirements-dev.txt
make run
```


## Multilingual interface
- Built-in languages: **Russian** (`ru`) and **English** (`en`).
- Use the language selector in **Settings**, or append `?lang=ru|en` to any URL.
- Selected language is stored in a cookie and restored automatically.

## GitHub collaboration language / Язык работы в GitHub
- GitHub templates are bilingual (EN/RU): Issue templates, PR template, and contributing docs.
- Шаблоны GitHub двуязычные (EN/RU): шаблоны issue, PR и документация для контрибьюторов.

## Requirements files
- Runtime dependencies: `requirements.txt`
- Development dependencies: `requirements-dev.txt`

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```


## Optional GitHub update check token
GitHub update checks are **best-effort** and work without any token.

If you want higher GitHub API limits, you may provide your **own** Personal Access Token:

```bash
export GITHUB_TOKEN=your_personal_token
```

- Token is optional and never required for app usage.
- Do not commit `.env` with secrets.

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
