"""Central logging configuration."""

from __future__ import annotations

import logging
from logging.config import dictConfig

from services.config import settings


def configure_logging() -> None:
    """Configure root and app loggers via dictConfig."""
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                    "level": "INFO",
                },
                "file": {
                    "class": "logging.FileHandler",
                    "formatter": "standard",
                    "level": "INFO",
                    "filename": str(settings.logs_dir / "app.log"),
                    "encoding": "utf-8",
                },
            },
            "root": {"handlers": ["console", "file"], "level": "INFO"},
        }
    )


def get_logger(name: str) -> logging.Logger:
    """Return logger by name."""
    return logging.getLogger(name)
