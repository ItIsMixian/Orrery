"""Feedback lifecycle state transitions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Feedback:
    due_at: int
    status: str = "pending"
    snoozed_until: int | None = None

    def auto_expire(self, now: int) -> None:
        if self.status == "pending" and now >= self.due_at:
            self.status = "expired"
            self.snoozed_until = max(self.snoozed_until or 0, now + 3600)

    def snooze(self, now: int, seconds: int) -> None:
        if seconds <= 0:
            raise ValueError("seconds must be positive")
        self.status = "snoozed"
        self.snoozed_until = now + seconds

    def tick(self, now: int) -> None:
        if self.status == "snoozed" and self.snoozed_until is not None and now >= self.snoozed_until:
            self.status = "pending"
            self.snoozed_until = None

    def should_prompt(self, now: int) -> bool:
        if self.status == "snoozed" and self.snoozed_until is not None and now < self.snoozed_until:
            return False
        return self.status == "pending"
