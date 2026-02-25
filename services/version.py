from datetime import datetime, timedelta
import subprocess

import requests

GITHUB_REPO_API = "https://api.github.com/repos/drakkoshkka/APKLife/commits/main"
_CACHE = {
    "expires_at": datetime.min,
    "data": {
        "local_commit": None,
        "remote_commit": None,
        "is_update_available": False,
        "status_text": "Проверка обновлений недоступна.",
    },
}


def _get_local_commit():
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        return None


def _get_remote_commit():
    try:
        response = requests.get(GITHUB_REPO_API, timeout=5)
        response.raise_for_status()
        payload = response.json()
        return (payload.get("sha") or "")[:7] or None
    except requests.RequestException:
        return None


def get_version_status():
    now = datetime.now()
    if now < _CACHE["expires_at"]:
        return _CACHE["data"]

    local_commit = _get_local_commit()
    remote_commit = _get_remote_commit()

    if local_commit and remote_commit:
        is_update_available = local_commit != remote_commit
        status_text = (
            "Доступно обновление из GitHub."
            if is_update_available
            else "Установлена актуальная версия из GitHub."
        )
    elif local_commit:
        is_update_available = False
        status_text = "Локальная версия определена, но проверить GitHub сейчас не удалось."
    else:
        is_update_available = False
        status_text = "Версия локального приложения не определена."

    data = {
        "local_commit": local_commit,
        "remote_commit": remote_commit,
        "is_update_available": is_update_available,
        "status_text": status_text,
    }
    _CACHE["data"] = data
    _CACHE["expires_at"] = now + timedelta(minutes=10)
    return data
