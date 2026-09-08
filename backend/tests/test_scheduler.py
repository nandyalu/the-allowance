"""Unit tests for _next_utc_time() (backend/tasks/scheduler.py) — quiv has no
cron/calendar scheduling, so the daily jobs approximate a fixed UTC time via
interval=86400 + run_at set by this helper to the next occurrence of that
time.

Renamed from _seconds_until 2026-09-08 when quiv 0.10.0 added run_at
(github.com/nandyalu/quiv#66): the helper used to return a delay in seconds,
computed against its own clock read, which quiv then read the clock again to
turn back into a deadline. Returning the instant itself removes that second
read.
"""
import datetime

import pytest

from backend.tasks.scheduler import _next_utc_time


def _fixed_now(monkeypatch, iso: str) -> None:
    fixed = datetime.datetime.fromisoformat(iso).replace(tzinfo=datetime.timezone.utc)

    class _FixedDatetime(datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed if tz else fixed.replace(tzinfo=None)

    monkeypatch.setattr(datetime, "datetime", _FixedDatetime)


def test_target_later_today(monkeypatch):
    _fixed_now(monkeypatch, "2026-08-05T10:00:00")
    assert _next_utc_time(21, 30) == datetime.datetime(2026, 8, 5, 21, 30, tzinfo=datetime.timezone.utc)


def test_target_already_passed_rolls_to_tomorrow(monkeypatch):
    _fixed_now(monkeypatch, "2026-08-05T22:00:00")
    # 21:30 already passed today -> next occurrence is tomorrow.
    assert _next_utc_time(21, 30) == datetime.datetime(2026, 8, 6, 21, 30, tzinfo=datetime.timezone.utc)


def test_target_equals_now_rolls_to_tomorrow(monkeypatch):
    _fixed_now(monkeypatch, "2026-08-05T21:30:00")
    assert _next_utc_time(21, 30) == datetime.datetime(2026, 8, 6, 21, 30, tzinfo=datetime.timezone.utc)


def test_grading_still_runs_after_the_sweep_it_used_to_share_a_slot_with():
    """morning_sweep was retired 2026-09-08 — the agent commissions its own
    research now, on its own schedule — but grading matured signals against
    the day's closing price is unrelated and still runs after the close."""
    from backend.tasks import scheduler as module

    assert not hasattr(module, "morning_sweep")
    assert hasattr(module, "daily_signals")
