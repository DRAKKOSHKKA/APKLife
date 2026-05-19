"""Domain exceptions for schedule loading and parsing flows."""


class ScheduleError(Exception):
    """Base domain exception for schedule operations."""


class ScheduleFetchError(ScheduleError):
    """Raised when schedule source cannot be reached or request fails."""


class ScheduleParseError(ScheduleError):
    """Raised when source data cannot be parsed into valid schedule."""


class ScheduleSchemaChangedError(ScheduleParseError):
    """Raised when source HTML schema no longer matches expected structure."""
