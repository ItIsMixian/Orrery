from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from orrery_fixture.feedback import Feedback


class FeedbackTests(unittest.TestCase):
    def test_snooze_suppresses_until_deadline(self) -> None:
        feedback = Feedback(due_at=100)
        feedback.snooze(now=10, seconds=20)
        self.assertFalse(feedback.should_prompt(29))
        feedback.tick(30)
        self.assertTrue(feedback.should_prompt(30))

    def test_future_feedback_remains_pending(self) -> None:
        feedback = Feedback(due_at=100)
        feedback.auto_expire(99)
        self.assertEqual(feedback.status, "pending")


if __name__ == "__main__":
    unittest.main()

