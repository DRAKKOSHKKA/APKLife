"""Pytest coverage for parser reliability, normalization and fallback behavior."""

from __future__ import annotations

from pathlib import Path

import pytest

from services.exceptions import ScheduleFetchError, ScheduleSchemaChangedError
from services.normalize import normalize_optional, normalize_text
from services.schedule_parser import parse_schedule_html
from services.utils_schedule import get_schedule

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_valid_page_success() -> None:
    result = parse_schedule_html(_fixture("valid_page.html"))
    assert "Пн 01.01" in result["schedule"]
    assert result["prev_week_id"] == 100
    assert result["next_week_id"] == 102


def test_problematic_realistic_html_is_parsed() -> None:
    result = parse_schedule_html(_fixture("problematic_realistic.html"))
    assert any("Понедельник" in day for day in result["days_list"])
    first_day = next(iter(result["schedule"]))
    assert result["schedule"][first_day][0][0]["subject"] == "Математика"


def test_empty_first_header_is_accepted() -> None:
    result = parse_schedule_html(_fixture("empty_first_header.html"))
    assert result["days_list"]


def test_no_thead_tbody_is_accepted_in_tolerant_mode() -> None:
    result = parse_schedule_html(_fixture("no_thead_tbody.html"))
    assert "Monday" in result["days_list"][0]


def test_schema_change_detection_missing_table() -> None:
    with pytest.raises(ScheduleSchemaChangedError):
        parse_schedule_html(_fixture("missing_table.html"))


def test_schema_change_detection_invalid_table() -> None:
    with pytest.raises(ScheduleSchemaChangedError):
        parse_schedule_html(_fixture("invalid_table.html"))


def test_schema_change_detection_changed_schema() -> None:
    with pytest.raises(ScheduleSchemaChangedError):
        parse_schedule_html(_fixture("changed_schema.html"))


def test_time_header_format_variations() -> None:
    result = parse_schedule_html(_fixture("problematic_realistic.html"))
    first_day = next(iter(result["schedule"]))
    assert result["schedule"][first_day][0][0]["time"] in {
        "08.00 - 09.30",
        "08:00-09:30",
        "08:00 - 09:30",
    }


def test_normalization_logic() -> None:
    assert normalize_text("  A   B ; C  ") == "A B , C"
    assert normalize_optional("   ") is None


def test_fallback_logic_returns_cache(monkeypatch) -> None:
    entity = {"SearchId": 1, "SearchString": "11 нмо", "OwnerId": 1, "Type": "group"}

    import services.utils_schedule as utils_schedule

    def fail_fetch(*_args, **_kwargs):
        raise ScheduleFetchError("fail")

    monkeypatch.setattr(utils_schedule, "fetch_network_schedule", fail_fetch)
    monkeypatch.setattr(
        utils_schedule,
        "get_schedule_cache",
        lambda _key: {
            "schedule": {
                "Пн": [
                    [
                        {
                            "time": "08:00-09:30",
                            "subject": "Алгебра",
                            "teacher": None,
                            "room": None,
                            "group": None,
                        }
                    ]
                ]
            },
            "days_list": ["Пн"],
            "prev_week_id": None,
            "next_week_id": None,
            "updated_at": "2025-01-01T00:00:00",
        },
    )

    schedule, _days, _prev, _next, meta = get_schedule(123, entity, prefer_cache=False)
    assert schedule
    assert meta["source"] == "cache"
    assert "warning" in meta and meta["warning"]
