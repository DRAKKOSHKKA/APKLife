"""HTML schedule source implementation based on remote site."""

from __future__ import annotations

from urllib.parse import quote

from services.config import settings
from services.http_client import http_client
from services.schedule_parser import parse_schedule_html
from services.sources.base import ScheduleSource
from services.types import ScheduleResult


class InstituteHtmlScheduleSource(ScheduleSource):
    """Concrete schedule source using it-institut.ru endpoints."""

    def fetch_html(self, week_id: int, entity_info: dict[str, object]) -> str:
        search_string = quote(str(entity_info["SearchString"]))
        url = settings.schedule_url_template.format(
            search_id=entity_info["SearchId"],
            search_string=search_string,
            owner_id=entity_info["OwnerId"],
            entity_type=entity_info["Type"],
            week_id=week_id,
        )
        return http_client.get_text(url)

    def parse(self, html: str) -> ScheduleResult:
        return parse_schedule_html(html)
