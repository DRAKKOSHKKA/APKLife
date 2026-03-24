"""Compatibility constants sourced from centralized settings."""

from services.config import settings

SEARCH_URL = settings.search_url
SCHEDULE_URL_TEMPLATE = settings.schedule_url_template
INTERNET_CHECK_URL = settings.internet_check_url
REQUEST_TIMEOUT_SECONDS = settings.request_timeout_seconds
INTERNET_CHECK_TIMEOUT_SECONDS = settings.internet_check_timeout_seconds
