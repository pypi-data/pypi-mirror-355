import unittest
from datetime import datetime, timedelta
from pastime import format_time

class TestFormatTime(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2024, 1, 1, 12, 0, 0)

    def test_just_now(self):
        dt = self.now - timedelta(seconds=30)
        self.assertEqual(format_time(dt, now=self.now), "just now")

    def test_minutes_ago(self):
        dt = self.now - timedelta(minutes=5)
        self.assertEqual(format_time(dt, now=self.now), "5 minutes ago")

    def test_hours_ago(self):
        dt = self.now - timedelta(hours=2)
        self.assertEqual(format_time(dt, now=self.now), "2 hours ago")

    def test_yesterday(self):
        dt = self.now - timedelta(days=1)
        self.assertTrue("yesterday at" in format_time(dt, now=self.now))

    def test_days_ago(self):
        dt = self.now - timedelta(days=3)
        self.assertEqual(format_time(dt, now=self.now), "3 days ago")

    def test_full_date(self):
        dt = self.now - timedelta(days=10)
        self.assertEqual(format_time(dt, now=self.now), dt.strftime("%b %d, %Y at %-I:%M %p"))

if __name__ == "__main__":
    unittest.main()
