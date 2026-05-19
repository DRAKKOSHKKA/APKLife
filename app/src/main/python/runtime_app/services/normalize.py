"""Normalization utilities used by parser and service layers."""

from __future__ import annotations

import re

_WHITESPACE = re.compile(r"\s+")


def normalize_text(value: str | None, *, lower: bool = False) -> str | None:
    """Normalize text by trimming and collapsing spaces, and optional lowercase."""
    if value is None:
        return None
    text = _WHITESPACE.sub(" ", value.strip())
    text = text.replace(";", ",")
    if not text:
        return None
    return text.lower() if lower else text


def normalize_optional(value: str | None) -> str | None:
    """Normalize string and map empty values to None."""
    return normalize_text(value)


def normalize_search(value: str | None) -> str:
    """Normalize search query text."""
    return normalize_text(value, lower=False) or ""
