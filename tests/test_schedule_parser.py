"""Unit tests for schedule parser functions."""

import unittest

from services.schedule_parser import parse_schedule_html, split_time_interval


class ScheduleParserTests(unittest.TestCase):
    def test_split_time_interval(self):
        parts = split_time_interval("08:00-09:30", 3)
        self.assertEqual(parts, ["08:00-08:30", "08:30-09:00", "09:00-09:30"])

    def test_parse_schedule_html_basic(self):
        html = """
        <table>
            <thead>
                <tr><th>День</th><th>08:00-09:30</th></tr>
            </thead>
            <tbody>
                <tr>
                    <th>Пн 01.01</th>
                    <td>
                        <div>
                            <span>Математика,</span>
                            <span>Иванов И.И., 101</span>
                            <span>11 нмо</span>
                        </div>
                    </td>
                </tr>
            </tbody>
        </table>
        <a href="#">prev</a>
        <a class="btn-primary" href="#">current</a>
        <a href="?WeekId=12345">next</a>
        """
        schedule, days_list, prev_week_id, next_week_id = parse_schedule_html(html)

        self.assertIn("Пн 01.01", schedule)
        self.assertEqual(days_list, ["Пн 01.01"])
        self.assertIsNone(prev_week_id)
        self.assertEqual(next_week_id, 12345)

        lesson = schedule["Пн 01.01"][0][0]
        self.assertEqual(lesson["subject"], "Математика,")
        self.assertEqual(lesson["teacher"], "Иванов И.И.")
        self.assertEqual(lesson["room"], "101")


if __name__ == "__main__":
    unittest.main()
