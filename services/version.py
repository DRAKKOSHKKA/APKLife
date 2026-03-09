"""GitHub version status provider with resilient, optional best-effort checks."""

from __future__ import annotations

import subprocess
from datetime import datetime, timedelta

from services.config import settings
from services.http_client import http_client
from services.logger import setup_logger

logger = setup_logger(__name__)

GITHUB_REPO_API = "https://api.github.com/repos/drakkoshkka/APKLife/commits/main"
GITHUB_RELEASES_API = "https://api.github.com/repos/drakkoshkka/APKLife/releases/latest"
_CACHE_TTL = timedelta(minutes=10)
_MAX_BACKOFF_SECONDS = 60 * 30
_BASE_BACKOFF_SECONDS = 60

_CACHE: dict[str, object] = {
    "expires_at": datetime.min,
    "next_allowed_check_at": datetime.min,
    "consecutive_failures": 0,
    "etag_remote_commit": None,
    "etag_release": None,
    "data": {
        "local_commit": None,
        "remote_commit": None,
        "latest_release": None,
        "is_update_available": False,
        "status_text": "Проверка обновлений недоступна.",
        "last_checked_at": None,
    },
}


def _utcnow() -> datetime:
    return datetime.utcnow()


def _github_headers(etag: str | None = None) -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": settings.github_api_user_agent,
    }
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    if etag:
        headers["If-None-Match"] = etag
    return headers


def _backoff_seconds(failures: int) -> int:
    computed = _BASE_BACKOFF_SECONDS * (2 ** max(failures, 0))
    return int(min(computed, _MAX_BACKOFF_SECONDS))


def _set_failure_backoff(reason: str) -> None:
    raw_failures = _CACHE.get("consecutive_failures", 0)
    failures = int(raw_failures) if isinstance(raw_failures, int | str) else 0
    failures += 1
    _CACHE["consecutive_failures"] = failures
    delay = _backoff_seconds(failures)
    _CACHE["next_allowed_check_at"] = _utcnow() + timedelta(seconds=delay)
    logger.warning(
        "version_check_backoff reason=%s failures=%s delay_seconds=%s", reason, failures, delay
    )


def _set_success() -> None:
    _CACHE["consecutive_failures"] = 0
    _CACHE["next_allowed_check_at"] = _utcnow()


def _get_local_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except FileNotFoundError:
        logger.warning("git_command_not_found_for_local_commit")
        return None
    except subprocess.SubprocessError:
        logger.info("local_commit_unavailable_not_a_git_repo_or_git_error")
        return None


def _extract_commit(payload: object) -> str | None:
    if isinstance(payload, dict):
        sha = payload.get("sha")
        if isinstance(sha, str) and sha:
            return sha[:7]
    return None


def _extract_release(payload: object) -> str | None:
    if isinstance(payload, dict):
        tag = payload.get("tag_name")
        if isinstance(tag, str) and tag:
            return tag
    return None


def _parse_rate_limit_reset(headers: dict[str, str]) -> datetime | None:
    reset_raw = headers.get("X-RateLimit-Reset")
    if not reset_raw:
        return None
    try:
        return datetime.utcfromtimestamp(int(reset_raw))
    except (ValueError, OSError):
        return None


def _fetch_remote_commit() -> tuple[str | None, bool, str | None]:
    etag = _CACHE.get("etag_remote_commit")
    status, payload, headers = http_client.get_json_with_meta(
        GITHUB_REPO_API,
        headers=_github_headers(str(etag) if isinstance(etag, str) else None),
        timeout=(settings.github_connect_timeout_seconds, settings.github_read_timeout_seconds),
    )

    if status == 304:
        cached = _CACHE["data"]
        cached_commit = cached.get("remote_commit") if isinstance(cached, dict) else None
        return cached_commit if isinstance(cached_commit, str) else None, True, None

    if status in (403, 429):
        remaining = headers.get("X-RateLimit-Remaining")
        if status == 429 or remaining == "0":
            reset_at = _parse_rate_limit_reset(headers)
            if reset_at:
                _CACHE["next_allowed_check_at"] = reset_at
            else:
                _set_failure_backoff("rate_limit")
            return None, False, "Лимит GitHub API исчерпан, повтор позже."

    if status >= 400:
        _set_failure_backoff(f"commit_http_{status}")
        return None, False, None

    if isinstance(payload, dict):
        etag_new = headers.get("ETag")
        if etag_new:
            _CACHE["etag_remote_commit"] = etag_new
        return _extract_commit(payload), False, None

    _set_failure_backoff("commit_invalid_payload")
    return None, False, None


def _fetch_latest_release() -> tuple[str | None, bool, str | None]:
    etag = _CACHE.get("etag_release")
    status, payload, headers = http_client.get_json_with_meta(
        GITHUB_RELEASES_API,
        headers=_github_headers(str(etag) if isinstance(etag, str) else None),
        timeout=(settings.github_connect_timeout_seconds, settings.github_read_timeout_seconds),
    )

    if status == 304:
        cached = _CACHE["data"]
        cached_release = cached.get("latest_release") if isinstance(cached, dict) else None
        return cached_release if isinstance(cached_release, str) else None, True, None

    if status in (403, 429):
        remaining = headers.get("X-RateLimit-Remaining")
        if status == 429 or remaining == "0":
            reset_at = _parse_rate_limit_reset(headers)
            if reset_at:
                _CACHE["next_allowed_check_at"] = reset_at
            else:
                _set_failure_backoff("rate_limit")
            return None, False, "Лимит GitHub API исчерпан, повтор позже."

    if status >= 400:
        _set_failure_backoff(f"release_http_{status}")
        return None, False, None

    if isinstance(payload, dict):
        etag_new = headers.get("ETag")
        if etag_new:
            _CACHE["etag_release"] = etag_new
        return _extract_release(payload), False, None

    _set_failure_backoff("release_invalid_payload")
    return None, False, None


def _compose_status_text(local_commit: str | None, remote_commit: str | None, failed: bool) -> str:
    if local_commit and remote_commit:
        return (
            "Доступно обновление из GitHub."
            if local_commit != remote_commit
            else "Установлена актуальная версия из GitHub."
        )
    if local_commit and failed:
        return "Не удалось проверить обновления (сеть/лимит)."
    if local_commit:
        return "Локальная версия определена, но данные GitHub временно недоступны."
    return "Версия локального приложения не определена (git не найден или не репозиторий)."


def get_version_status() -> dict[str, object]:
    now = _utcnow()
    cached_data = _CACHE.get("data")
    if not isinstance(cached_data, dict):
        cached_data = {}

    expires_at = _CACHE.get("expires_at")
    if isinstance(expires_at, datetime) and now < expires_at:
        return cached_data

    next_allowed = _CACHE.get("next_allowed_check_at")
    if isinstance(next_allowed, datetime) and now < next_allowed:
        local_commit = _get_local_commit()
        data = {
            **cached_data,
            "local_commit": local_commit,
            "is_update_available": bool(
                local_commit
                and isinstance(cached_data.get("remote_commit"), str)
                and local_commit != cached_data.get("remote_commit")
            ),
            "status_text": "Не удалось проверить обновления (сеть/лимит).",
            "last_checked_at": now.isoformat(timespec="seconds"),
        }
        _CACHE["data"] = data
        _CACHE["expires_at"] = now + _CACHE_TTL
        return data

    local_commit = _get_local_commit()
    had_failure = False
    rate_limit_message: str | None = None

    try:
        remote_commit, commit_from_cache, commit_message = _fetch_remote_commit()
        latest_release, release_from_cache, release_message = _fetch_latest_release()

        if commit_message:
            rate_limit_message = commit_message
        if release_message:
            rate_limit_message = release_message

        if remote_commit is None and not commit_from_cache:
            had_failure = True
        if latest_release is None and not release_from_cache:
            had_failure = True

        if had_failure and not rate_limit_message:
            _set_failure_backoff("github_partial_failure")
        elif not had_failure:
            _set_success()

        status_text = rate_limit_message or _compose_status_text(
            local_commit, remote_commit, had_failure
        )
        data = {
            "local_commit": local_commit,
            "remote_commit": remote_commit,
            "latest_release": latest_release,
            "is_update_available": bool(
                local_commit and remote_commit and local_commit != remote_commit
            ),
            "status_text": status_text,
            "last_checked_at": now.isoformat(timespec="seconds"),
        }
        _CACHE["data"] = data
        _CACHE["expires_at"] = now + _CACHE_TTL
        return data
    except Exception:  # noqa: BLE001
        logger.exception("unexpected_version_check_failure")
        _set_failure_backoff("unexpected_exception")
        data = {
            "local_commit": local_commit,
            "remote_commit": None,
            "latest_release": None,
            "is_update_available": False,
            "status_text": "Не удалось проверить обновления (сеть/лимит).",
            "last_checked_at": now.isoformat(timespec="seconds"),
        }
        _CACHE["data"] = data
        _CACHE["expires_at"] = now + _CACHE_TTL
        return data
