"""Service for generating mock data for debugging purposes."""

from __future__ import annotations

def get_mock_schedule(mode: str) -> dict | list | str:
    if mode == "empty":
        return {"days": [], "group_name": "MOCK_EMPTY"}

    if mode == "long":
        items = []
        for i in range(50):
            items.append({
                "Number": str(i+1),
                "Time": "08:30 - 09:50",
                "Subject": f"Extreme Long Subject Name Lesson #{i+1}",
                "Teacher": "Professor Stress Tester",
                "Room": f"Room {i*100}",
                "IsCurrent": False
            })
        return {
            "days": [{"Date": "Mock Date", "DayName": "Monday", "Lessons": items}],
            "group_name": "MOCK_LONG"
        }

    if mode == "broken":
        return "{'invalid_json': true, missing_quotes: 123"

    if mode == "duplicates":
        lesson = {
            "Number": "1",
            "Time": "08:30 - 09:50",
            "Subject": "Duplicate Subject",
            "Teacher": "Teacher X",
            "Room": "101",
            "IsCurrent": False
        }
        return {
            "days": [{"Date": "Mock Date", "DayName": "Monday", "Lessons": [lesson, lesson, lesson]}],
            "group_name": "MOCK_DUPLICATES"
        }

    return None
