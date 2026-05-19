"""
Android entrypoint: запускает локальный Flask-сервер внутри Chaquopy.

Этот модуль вызывается из Kotlin через Chaquopy API:
    val module = py.getModule("android_entry")
    module.callAttr("start_server")

Flask-сервер запускается в отдельном daemon-потоке на 127.0.0.1:5000,
после чего MainActivity подключается к нему через WebView.
"""

from __future__ import annotations

import os
import sys
import threading
from pathlib import Path

# Флаг защиты от повторного запуска сервера
_SERVER_STARTED = False
_LOCK = threading.Lock()


def _runtime_root() -> Path:
    """Вычисляет путь к копии Flask-приложения внутри APK."""
    return Path(__file__).resolve().parent / "runtime_app"


def start_server() -> None:
    """
    Запускает Flask-сервер один раз в фоновом daemon-потоке.

    Функция thread-safe: повторные вызовы игнорируются благодаря
    глобальному флагу _SERVER_STARTED и мьютексу _LOCK.

    Шаги:
    1. Добавляет runtime_app/ в sys.path, чтобы Python нашёл наш код
    2. Устанавливает рабочую директорию для templates и static
    3. Импортирует create_app() из app.py
    4. Запускает Flask app.run() в daemon-потоке
    """
    global _SERVER_STARTED  # noqa: PLW0603

    with _LOCK:
        if _SERVER_STARTED:
            return

        runtime_root = _runtime_root()

        # Добавляем путь к нашему Flask-приложению
        sys.path.insert(0, str(runtime_root))

        # Устанавливаем рабочую директорию — Flask ищет templates/ и static/ здесь
        os.chdir(str(runtime_root))

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
