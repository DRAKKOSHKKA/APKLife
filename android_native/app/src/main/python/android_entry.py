"""Android entrypoint: boot local Flask server inside Chaquopy runtime."""

from __future__ import annotations

import sys
import threading
from pathlib import Path

_SERVER_STARTED = False
_LOCK = threading.Lock()


def _runtime_root() -> Path:
    return Path(__file__).resolve().parent / "runtime_app"


def start_server() -> None:
    """Start Flask server once in background thread."""
    global _SERVER_STARTED

    with _LOCK:
        if _SERVER_STARTED:
            return

        runtime_root = _runtime_root()
        sys.path.insert(0, str(runtime_root))

        from app import create_app

        app = create_app()

        thread = threading.Thread(
            target=app.run,
            kwargs={
                "host": "127.0.0.1",
                "port": 5000,
                "debug": False,
                "use_reloader": False,
                "threaded": True,
            },
            daemon=True,
        )
        thread.start()
        _SERVER_STARTED = True
