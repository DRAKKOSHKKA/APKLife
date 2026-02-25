from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict

import requests

from services.cache_store import load_version_cache, save_version_cache

REPO_API_COMMIT = "https://api.github.com/repos/drakkoshkka/APKLife/commits/main"
VERSION_CACHE_TTL = timedelta(hours=1)


def _get_local_commit() -> str:
    head = Path('.git/HEAD')
    if not head.exists():
        return "unknown"

    try:
        head_data = head.read_text(encoding='utf-8').strip()
        if head_data.startswith('ref:'):
            ref_path = Path('.git') / head_data.split(' ', 1)[1]
            if ref_path.exists():
                return ref_path.read_text(encoding='utf-8').strip()[:7]
            return "unknown"
        return head_data[:7]
    except OSError:
        return "unknown"


def _fetch_remote_commit() -> str:
    response = requests.get(REPO_API_COMMIT, timeout=5)
    response.raise_for_status()
    data = response.json()
    return data.get('sha', '')[:7] or "unknown"


def get_version_status() -> Dict[str, str]:
    local_commit = _get_local_commit()
    now = datetime.now()

    cache = load_version_cache()
    cached_at_raw = cache.get('checked_at')
    remote_commit = cache.get('remote_commit')

    if cached_at_raw and remote_commit:
        try:
            cached_at = datetime.fromisoformat(cached_at_raw)
            if now - cached_at < VERSION_CACHE_TTL:
                status = "up-to-date" if remote_commit == local_commit else "update-available"
                return {
                    "local_commit": local_commit,
                    "remote_commit": remote_commit,
                    "status": status,
                    "checked_at": cached_at.strftime('%d.%m.%Y %H:%M'),
                }
        except ValueError:
            pass

    try:
        remote_commit = _fetch_remote_commit()
        save_version_cache({
            "remote_commit": remote_commit,
            "checked_at": now.isoformat(timespec='seconds'),
        })
        status = "up-to-date" if remote_commit == local_commit else "update-available"
    except requests.RequestException:
        status = "offline"
        remote_commit = remote_commit or "unknown"

    return {
        "local_commit": local_commit,
        "remote_commit": remote_commit,
        "status": status,
        "checked_at": now.strftime('%d.%m.%Y %H:%M'),
    }
