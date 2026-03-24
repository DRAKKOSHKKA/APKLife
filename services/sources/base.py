"""Abstract source interfaces for schedule providers."""

from __future__ import annotations

from typing import Protocol

from services.types import ScheduleResult


class ScheduleSource(Protocol):
    """Contract for schedule source providers."""

    def fetch_html(self, week_id: int, entity_info: dict[str, object]) -> str:
        """Fetch source HTML for given week/entity."""

    def parse(self, html: str) -> ScheduleResult:
        """Parse source HTML into normalized schedule result."""
