import sqlite3
import tempfile
import unittest
from pathlib import Path

from orrery_fixture.feedback import Feedback
from orrery_fixture.storage import SCHEMA_VERSION, initialize_database


class ApplicationBaselineTests(unittest.TestCase):
    def test_future_feedback_remains_pending(self):
        feedback = Feedback(due_at=20)
        feedback.auto_expire(10)
        self.assertEqual("pending", feedback.status)

    def test_explicit_snooze_round_trip(self):
        feedback = Feedback(due_at=20)
        feedback.snooze(10, 30)
        feedback.tick(40)
        self.assertEqual("pending", feedback.status)
        self.assertIsNone(feedback.snoozed_until)

    def test_storage_selects_its_declared_schema(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "app.db"
            initialize_database(path)
            connection = sqlite3.connect(path)
            try:
                version = connection.execute("PRAGMA user_version").fetchone()[0]
            finally:
                connection.close()
            self.assertEqual(SCHEMA_VERSION, version)

    def test_storage_initialization_is_repeatable(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "app.db"
            initialize_database(path)
            initialize_database(path)


if __name__ == "__main__":
    unittest.main()
