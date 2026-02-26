# APKLife Architecture

## Layered architecture
1. **Presentation layer** (`routes/*`)
   - Validates input
   - Calls services
   - Returns HTML/JSON responses
2. **Service layer** (`services/schedule.py`, `services/utils_schedule.py`)
   - Business orchestration
   - Fallback logic and metadata
3. **Source layer** (`services/sources/*`, `services/http_client.py`, `services/schedule_parser.py`)
   - External fetching and parsing
4. **Cache layer** (`services/cache_store.py`)
   - Local persistence and history snapshots
5. **Utility layer** (`services/normalize.py`, `services/validators.py`, `services/logging_config.py`)
   - Cross-cutting helpers

## Rules
- Routes must not perform network calls.
- Routes must not mutate cache directly.
- Source implementations must satisfy `ScheduleSource` protocol.
- Domain failures use typed exceptions only.

## SOLID focus
- SRP: parsing/fetching/cache/normalization split into dedicated modules.
- OCP: new providers can implement `ScheduleSource` without changing orchestration.
- DIP: orchestration depends on `ScheduleSource` abstraction.
