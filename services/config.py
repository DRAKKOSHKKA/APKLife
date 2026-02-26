"""Centralized application configuration with environment overrides."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "APKLife")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")
    host: str = os.getenv("APP_HOST", "0.0.0.0")
    port: int = int(os.getenv("APP_PORT", "5000"))
    debug: bool = os.getenv("APP_DEBUG", "true").lower() == "true"
    search_url: str = os.getenv("SEARCH_URL", "https://it-institut.ru/SearchString/KeySearch")
    schedule_url_template: str = os.getenv(
        "SCHEDULE_URL_TEMPLATE",
        "https://it-institut.ru/Raspisanie/SearchedRaspisanie"
        "?SearchId={search_id}&SearchString={search_string}&Type={entity_type}&OwnerId={owner_id}&WeekId={week_id}",
    )
    internet_check_url: str = os.getenv("INTERNET_CHECK_URL", "https://www.google.com/generate_204")
    request_timeout_seconds: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "15"))
    internet_check_timeout_seconds: int = int(os.getenv("INTERNET_CHECK_TIMEOUT_SECONDS", "3"))
    connect_timeout_seconds: int = int(os.getenv("CONNECT_TIMEOUT_SECONDS", "5"))
    read_timeout_seconds: int = int(os.getenv("READ_TIMEOUT_SECONDS", "15"))
    github_token: str = os.getenv("GITHUB_TOKEN", "").strip()
    github_api_user_agent: str = os.getenv("GITHUB_API_USER_AGENT", "APKLife")
    github_connect_timeout_seconds: int = int(
        os.getenv("GITHUB_CONNECT_TIMEOUT_SECONDS", os.getenv("CONNECT_TIMEOUT_SECONDS", "5"))
    )
    github_read_timeout_seconds: int = int(
        os.getenv("GITHUB_READ_TIMEOUT_SECONDS", os.getenv("READ_TIMEOUT_SECONDS", "15"))
    )
    retry_total: int = int(os.getenv("HTTP_RETRY_TOTAL", "3"))
    retry_backoff: float = float(os.getenv("HTTP_RETRY_BACKOFF", "0.5"))
    cache_dir: Path = Path(os.getenv("CACHE_DIR", "cache"))
    cache_file: Path = Path(os.getenv("CACHE_FILE", "cache/schedule_cache.json"))
    failed_html_dir: Path = Path(os.getenv("FAILED_HTML_DIR", "data/failed_html"))
    logs_dir: Path = Path(os.getenv("LOGS_DIR", "logs"))


settings = Settings()
