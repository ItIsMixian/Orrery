"""Feedback lifecycle with an intentionally injected auto-expiry defect."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Feedback:
    due_at: int
    status: str = "pending"
    snoozed_until: int | None = None

    def snooze(self, now: int, duration: int) -> None:
        self.status = "snoozed"
        self.snoozed_until = now + duration

    def auto_expire(self, now: int) -> None:
        if self.status == "pending" and now >= self.due_at:
            self.status = "expired"
            self.snoozed_until = max(self.snoozed_until or 0, now + 3600)

    def tick(self, now: int) -> None:
        if self.status == "snoozed" and self.snoozed_until is not None and now >= self.snoozed_until:
            self.status = "pending"
            self.snoozed_until = None

    def should_prompt(self, now: int) -> bool:
        self.tick(now)
        return self.status == "pending" and now < self.due_at
