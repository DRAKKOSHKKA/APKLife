"""HTTP client with retries, timeouts and domain-level exception mapping."""

from __future__ import annotations

from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from services.config import settings
from services.exceptions import ScheduleFetchError
from services.logging_config import get_logger

logger = get_logger(__name__)


class HttpClient:
    """Wrapper around requests.Session with retry policy."""

    def __init__(self) -> None:
        self.session = requests.Session()
        retries = Retry(
            total=settings.retry_total,
            connect=settings.retry_total,
            read=settings.retry_total,
            backoff_factor=settings.retry_backoff,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET", "HEAD"),
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def get_text(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        timeout: tuple[int, int] | None = None,
    ) -> str:
        """GET URL and return response text."""
        try:
            response = self.session.get(
                url,
                params=params,
                timeout=timeout
                or (settings.connect_timeout_seconds, settings.read_timeout_seconds),
            )
            response.raise_for_status()
            response.encoding = "utf-8"
            logger.info("http_get_success url=%s status=%s", response.url, response.status_code)
            return response.text
        except requests.RequestException as exc:
            logger.exception("http_get_failed url=%s", url)
            raise ScheduleFetchError(f"Network request failed for {url}") from exc

    def get_json(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        timeout: tuple[int, int] | None = None,
    ) -> Any:
        """GET URL and return JSON payload."""
        try:
            response = self.session.get(
                url,
                params=params,
                timeout=timeout
                or (settings.connect_timeout_seconds, settings.read_timeout_seconds),
            )
            response.raise_for_status()
            logger.info(
                "http_get_json_success url=%s status=%s", response.url, response.status_code
            )
            return response.json()
        except requests.RequestException as exc:
            logger.exception("http_get_json_failed url=%s", url)
            raise ScheduleFetchError(f"Network request failed for {url}") from exc
        except ValueError as exc:
            logger.exception("http_json_decode_failed url=%s", url)
            raise ScheduleFetchError(f"Invalid JSON from {url}") from exc


http_client = HttpClient()
