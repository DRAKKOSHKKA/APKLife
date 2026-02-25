# Contributing to APKLife

## Environment setup
1. Install Python 3.11+.
2. Create virtualenv: `python -m venv .venv`.
3. Activate virtualenv and install deps: `make install`.

## Running locally
- `make run`
- App opens on `http://127.0.0.1:5000`.

## Running tests
- `make test`

## Linting and static checks
- `make lint`

## Branching strategy
- Branch from `main` using `feature/<topic>`.
- Keep commits small and focused.
- Rebase on top of `origin/main` before PR.

## Pull request rules
- Provide motivation + technical summary.
- Include test/lint output.
- Do not merge with failing CI.

## Code style expectations
- Use Black formatting.
- Keep functions small and single-purpose.
- No wildcard imports.
- Add type hints in service layer.
