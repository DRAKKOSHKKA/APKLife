# APKLife Project Structure (EN)

This file explains where each part of the repository lives and what it is responsible for.

## Top-level
- `app.py` — Flask app entrypoint and app wiring.
- `config.py` — compatibility config bridge.
- `bridge.py` — Android Variant A build bridge (Capacitor wrapper).
- `Makefile` — developer commands (`install`, `test`, `lint`, `run`).
- `pyproject.toml` — project metadata and tooling config.
- `requirements.txt` / `requirements-dev.txt` — runtime/dev dependencies.
- `.env.example` — environment variable template.

## Core backend
- `routes/`
  - `main.py` — index + health routes.
  - `group.py` — schedule page + refresh/metrics/logs endpoints.
- `services/`
  - `config.py` — typed runtime settings.
  - `http_client.py` — HTTP wrapper with retries/timeouts and metadata fetch.
  - `schedule_parser.py` — schedule HTML parser and schema heuristics.
  - `utils_schedule.py` — cache-first orchestration and source fallback.
  - `schedule.py` — route-facing schedule context builder.
  - `cache_store.py` — cache persistence/history.
  - `version.py` — optional GitHub update status (best-effort).
  - `i18n.py` — UI/backend localization helpers.
  - `metrics.py`, `runtime_state.py` — diagnostics and runtime status.
  - `logging_config.py`, `logger.py` — structured logging.
  - `validators.py`, `normalize.py` — data hygiene helpers.
  - `exceptions.py`, `types.py` — domain errors and typed contracts.
  - `sources/` — source abstraction and HTML source adapter.

## Frontend
- `templates/` — Jinja templates (base/index/group/errors/partials).
- `static/`
  - `style.css` — app styles.
  - `scripts.js` — frontend interactions, dev mode, SW registration.
  - `sw.js`, `manifest.webmanifest` — PWA support.
  - `suggestions.json` — local autocomplete data.

## Mobile wrappers
- `android_native/` — Variant B (Chaquopy, Flask inside APK).
- `android_bridge/` — Variant A generated bridge assets (when built locally).

## Tests
- `tests/test_schedule_parser.py` — parser reliability test suite.
- `tests/test_version.py` — GitHub version check resiliency tests.
- `tests/fixtures/` — HTML fixtures for parser scenarios.

## Documentation
- `README*.md` — project overview by language.
- `CONTRIBUTING*.md` — contribution guidelines by language.
- `CODE_OF_CONDUCT*.md` — community rules by language.
- `docs/ARCHITECTURE*.md` — architecture docs by language.
- `docs/PROJECT_STRUCTURE*.md` — this structure map by language.
- `.github/*` — bilingual issue and PR templates.

Back: [README.en.md](../README.en.md)
