"""Application constants for remote schedule integration."""

SEARCH_URL = "https://it-institut.ru/SearchString/KeySearch"
SCHEDULE_URL_TEMPLATE = (
    "https://it-institut.ru/Raspisanie/SearchedRaspisanie"
    "?SearchId={search_id}&SearchString={search_string}&Type={entity_type}&OwnerId={owner_id}&WeekId={week_id}"
)
INTERNET_CHECK_URL = "https://www.google.com/generate_204"
REQUEST_TIMEOUT_SECONDS = 15
INTERNET_CHECK_TIMEOUT_SECONDS = 3
