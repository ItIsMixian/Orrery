from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from orrery_fixture.storage import initialize_database


class StorageTests(unittest.TestCase):
    def test_fresh_database_has_feedback_table(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "app.db"
            initialize_database(path)
            connection = sqlite3.connect(path)
            try:
                table = connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='feedback'"
                ).fetchone()
            finally:
                connection.close()
            self.assertIsNotNone(table)

    def test_repeated_v1_initialization_is_safe(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "app.db"
            initialize_database(path)
            initialize_database(path)
            connection = sqlite3.connect(path)
            try:
                version = connection.execute("PRAGMA user_version").fetchone()[0]
            finally:
                connection.close()
            self.assertEqual(version, 1)


if __name__ == "__main__":
    unittest.main()
