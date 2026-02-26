from __future__ import annotations

from datetime import datetime

import services.version as version
from services.exceptions import ScheduleFetchError


def _reset_cache() -> None:
    version._CACHE["expires_at"] = datetime.min
    version._CACHE["next_allowed_check_at"] = datetime.min
    version._CACHE["consecutive_failures"] = 0
    version._CACHE["etag_remote_commit"] = None
    version._CACHE["etag_release"] = None
    version._CACHE["data"] = {
        "local_commit": None,
        "remote_commit": None,
        "latest_release": None,
        "is_update_available": False,
        "status_text": "Проверка обновлений недоступна.",
        "last_checked_at": None,
    }


def test_version_status_github_unavailable(monkeypatch) -> None:
    _reset_cache()
    monkeypatch.setattr(version, "_get_local_commit", lambda: "abc1234")

    def _fail(*_args, **_kwargs):
        raise ScheduleFetchError("offline")

    monkeypatch.setattr(version.http_client, "get_json_with_meta", _fail)

    payload = version.get_version_status()
    assert payload["local_commit"] == "abc1234"
    assert payload["remote_commit"] is None
    assert payload["latest_release"] is None
    assert payload["is_update_available"] is False
    assert isinstance(payload["status_text"], str)
    assert payload["last_checked_at"] is not None


def test_version_status_not_modified_uses_cache(monkeypatch) -> None:
    _reset_cache()
    version._CACHE["etag_remote_commit"] = '"commit-etag"'
    version._CACHE["etag_release"] = '"release-etag"'
    version._CACHE["data"] = {
        "local_commit": "1111111",
        "remote_commit": "aaaaaaa",
        "latest_release": "v1.2.3",
        "is_update_available": True,
        "status_text": "cached",
        "last_checked_at": None,
    }
    monkeypatch.setattr(version, "_get_local_commit", lambda: "1111111")

    calls = {"count": 0}

    def _meta(*_args, **_kwargs):
        calls["count"] += 1
        return 304, None, {}

    monkeypatch.setattr(version.http_client, "get_json_with_meta", _meta)

    payload = version.get_version_status()
    assert calls["count"] == 2
    assert payload["remote_commit"] == "aaaaaaa"
    assert payload["latest_release"] == "v1.2.3"


def test_version_status_rate_limit_sets_next_allowed(monkeypatch) -> None:
    _reset_cache()
    monkeypatch.setattr(version, "_get_local_commit", lambda: "abc1234")

    responses = [
        (403, None, {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1893456000"}),
        (304, None, {}),
    ]

    def _meta(*_args, **_kwargs):
        return responses.pop(0)

    monkeypatch.setattr(version.http_client, "get_json_with_meta", _meta)

    payload = version.get_version_status()
    assert payload["is_update_available"] is False
    assert "Лимит GitHub API исчерпан" in str(payload["status_text"])

    next_allowed = version._CACHE.get("next_allowed_check_at")
    assert isinstance(next_allowed, datetime)
    assert next_allowed > datetime.utcnow()
