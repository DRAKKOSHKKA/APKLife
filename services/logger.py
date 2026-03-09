"""Backward-compatible logger helpers."""

from services.logging_config import configure_logging, get_logger

configure_logging()


def setup_logger(name: str):
    """Return configured logger."""
    return get_logger(name)
