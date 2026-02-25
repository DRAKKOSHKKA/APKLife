"""Logging configuration for APKLife services."""

import logging
from pathlib import Path


def setup_logger(name: str) -> logging.Logger:
    """Create (or get) a configured logger with console+file handlers."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    log_level = logging.DEBUG
    logger.setLevel(log_level)

    log_format = "%(asctime)s [%(levelname)s] %(name)s %(filename)s:%(lineno)d :: %(message)s"
    formatter = logging.Formatter(log_format)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger.propagate = False
    return logger
