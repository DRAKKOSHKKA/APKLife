# Contributing to APKLife (EN)

## 1) Environment setup

### Linux/macOS

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

## 2) Run locally

```bash
make run
```

## 3) Quality checks

```bash
make test
make lint
```

## 4) Branching strategy

* Branch from `main` with `feature/<topic>` or `fix/<topic>`.
* Keep commits focused and atomic.
* Rebase your branch on top of `origin/main` before PR.

## 5) Pull request expectations

* Explain motivation and technical approach.
* Include validation commands and outcomes.
* Update docs when behavior/config changes.
* Ensure no secrets/tokens are committed.

## 6) Coding expectations

* Use Black formatting.
* Pass Ruff and Mypy checks.
* Keep service modules cohesive (single responsibility).
* Avoid wildcard imports.
