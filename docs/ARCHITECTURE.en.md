# APKLife Architecture (EN)

## Layered design
1. **Presentation layer**: `routes/*`, `templates/*`, `static/*`
2. **Service layer**: `services/schedule.py`, `services/utils_schedule.py`, `services/version.py`
3. **Source layer**: `services/sources/*`, `services/http_client.py`, `services/schedule_parser.py`
4. **Cache layer**: `services/cache_store.py`
5. **Utility layer**: `services/normalize.py`, `services/validators.py`, `services/logging_config.py`

## Core principles
- Routes validate input and return responses.
- Routes must not make direct network calls.
- Routes must not mutate cache directly.
- External source logic stays behind source/parser/http abstractions.

## Reliability patterns
- Typed domain errors in `services/exceptions.py`.
- Retry + timeout in `services/http_client.py`.
- Schema-aware parsing with diagnostics and snapshot fallback in `services/schedule_parser.py`.
- Cache-first behavior in `services/utils_schedule.py`.

## Observability
- Structured logs via `services/logging_config.py`.
- Runtime metrics via `services/metrics.py`.
- Health endpoint in `routes/main.py`.

## Extension points
- New schedule providers can implement `services/sources/base.py` interface.
- UI translations are managed through `services/i18n.py`.

Back: [README.en.md](../README.en.md)
