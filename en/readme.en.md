# APKLife (English)

APKLife is a Flask-based student schedule application with:

* cache-first loading,
* offline fallback,
* resilient HTML parser,
* optional GitHub update checks,
* PWA support,
* Android build variants.

## Documentation map

* [Architecture](architecture.en.md)
* [Contributing guide](contributing.en.md)
* [Code of Conduct](code_of_conduct.en.md)
* [Android Native (Variant B)](readme.en-1.md)

## Quick start

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

App URL: `http://127.0.0.1:5000`

## Core commands

```bash
make test
make lint
```

## Environment variables

Use `.env.example` as template.

Important settings:

* App: `APP_HOST`, `APP_PORT`, `APP_DEBUG`
* HTTP timeouts: `CONNECT_TIMEOUT_SECONDS`, `READ_TIMEOUT_SECONDS`
* Cache and diagnostics: `CACHE_FILE`, `FAILED_HTML_DIR`, `LOGS_DIR`
* Optional GitHub checks: `GITHUB_TOKEN`, `GITHUB_API_USER_AGENT`, `GITHUB_CONNECT_TIMEOUT_SECONDS`, `GITHUB_READ_TIMEOUT_SECONDS`

## Optional GitHub token (never required)

GitHub update checks are **best-effort** and work without any token.

If you want higher GitHub API rate limits, set your own PAT locally:

```bash
export GITHUB_TOKEN=your_personal_token
```

Windows (PowerShell):

```powershell
$env:GITHUB_TOKEN="your_personal_token"
```

Security notes:

* Never commit secrets.
* `.env` is ignored by git.

## Android build

### Variant A: Capacitor wrapper

```bash
python bridge.py --base-url https://example.com --debug
python bridge.py --base-url https://example.com --release
python bridge.py --base-url https://example.com --release --aab
```

Expected artifacts:

* `android_bridge/android/app/build/outputs/apk/debug/app-debug.apk`
* `android_bridge/android/app/build/outputs/apk/release/app-release.apk`
* `android_bridge/android/app/build/outputs/bundle/release/app-release.aab`

### Variant B: Offline Flask-in-APK

See: [README.md](readme.en-1.md)

## Troubleshooting

* Parser snapshots on schema failures: `data/failed_html/`
* App logs: `logs/app.log`
* Health endpoint: `/health`

[Back to language switch](../)
