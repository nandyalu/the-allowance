"""Today's bar is summed from the 1-minute cache instead of re-fetched.

The watchdog captures 1-minute bars for every tracked ticker on the same tick
that asks for the day's bar, so the answer is usually already on disk. Asking
Webull for it again was most of what pushed this app over the market-data rate
limit on 2026-09-09 — 192 refused daily-bar fetches in one day, while seven of
ten tickers held the whole session in the table the same tick had just
written.

A bar summed from real minutes is also better than a vendor's in-progress
daily bar, not merely cheaper. The one thing it must never do is report a
partial day as a whole one.
"""
import datetime

import pytest

from backend.services import bars
from backend.services.watchdog import US_MARKET_TZ

TODAY = datetime.date(2026, 9, 9)  # a Wednesday


def _minute(at: datetime.datetime, o, h, lo, c, v):
    class _Row:
        timestamp = at
        open = o
        high = h
        low = lo
        close = c
        volume = v

    return _Row()


def _session_minute(minutes_in: int, o, h, lo, c, v):
    """A bar that many minutes after the opening bell, in UTC."""
    opened = datetime.datetime.combine(
        TODAY, datetime.time(9, 30), tzinfo=US_MARKET_TZ
    ).astimezone(datetime.timezone.utc)
    return _minute(opened + datetime.timedelta(minutes=minutes_in), o, h, lo, c, v)


@pytest.fixture
def cached_minutes(monkeypatch):
    def set_minutes(rows):
        monkeypatch.setattr(bars.db, "get_intraday_bars", lambda ticker, start, end=None: rows)

    return set_minutes


@pytest.fixture(autouse=True)
def never_fetch(monkeypatch):
    """Any live fetch in these tests is a failure to derive — make it obvious
    rather than letting a network call decide the assertion."""
    monkeypatch.setattr(bars, "_fetch_history", lambda *a, **k: pytest.fail("fetched"))
    monkeypatch.setattr(bars.listings, "should_fetch", lambda ticker: True)


def test_a_covered_session_is_summed_from_the_minutes(cached_minutes):
    cached_minutes([
        _session_minute(0, 100.0, 101.0, 99.5, 100.5, 1_000),
        _session_minute(1, 100.5, 104.0, 100.0, 103.0, 2_000),
        _session_minute(2, 103.0, 103.5, 97.0, 98.0, 3_000),
    ])

    bar = bars._todays_bar_from_minutes("NVDA", TODAY)

    assert bar is not None
    assert bar.open == 100.0  # the first minute's open, not the lowest
    assert bar.high == 104.0
    assert bar.low == 97.0
    assert bar.close == 98.0  # the last minute's close, not the highest
    assert bar.volume == 6_000
    assert bar.date == "2026-09-09"


def test_todays_bar_prefers_the_minutes_over_a_fetch(cached_minutes):
    """The whole point: _fetch_history would fail this test if it ran."""
    cached_minutes([_session_minute(0, 100.0, 101.0, 99.0, 100.5, 1_000)])

    bar = bars._todays_bar("NVDA", TODAY)

    assert bar is not None
    assert bar.close == 100.5


def test_a_cache_that_misses_the_open_is_refused(cached_minutes, monkeypatch):
    """SMCI on 2026-09-09 held 30 minutes starting at 14:28, an hour into the
    session. Summing those would have reported 14:28's price as the day's open
    and its range as the day's high and low."""
    cached_minutes([
        _session_minute(58, 39.6, 40.1, 39.58, 40.0, 500),
        _session_minute(59, 40.0, 40.2, 39.9, 40.1, 500),
    ])

    assert bars._todays_bar_from_minutes("SMCI", TODAY) is None


def test_an_empty_cache_is_refused(cached_minutes):
    cached_minutes([])
    assert bars._todays_bar_from_minutes("TSLA", TODAY) is None


def test_a_bar_stamped_a_little_late_still_counts_as_the_open(cached_minutes):
    """A bar a few seconds after the bell is the same bar. Only a real gap
    means the cache missed the open."""
    opened = datetime.datetime.combine(
        TODAY, datetime.time(9, 30), tzinfo=US_MARKET_TZ
    ).astimezone(datetime.timezone.utc)
    cached_minutes([
        _minute(opened + datetime.timedelta(seconds=40), 100.0, 101.0, 99.0, 100.5, 1_000),
    ])

    assert bars._todays_bar_from_minutes("NVDA", TODAY) is not None


def test_yesterdays_minutes_do_not_count_as_today(cached_minutes):
    """get_intraday_bars is open-ended on its end, so a row from another day
    reaching this function must be dropped rather than summed into today."""
    yesterday = datetime.datetime.combine(
        TODAY - datetime.timedelta(days=1), datetime.time(9, 30), tzinfo=US_MARKET_TZ
    ).astimezone(datetime.timezone.utc)
    cached_minutes([_minute(yesterday, 1.0, 1.0, 1.0, 1.0, 1)])

    assert bars._todays_bar_from_minutes("NVDA", TODAY) is None


def test_the_weekend_is_still_skipped_before_anything_is_read(cached_minutes):
    """The weekend guard runs first, so a Saturday costs neither a query nor a
    request."""
    saturday = datetime.date(2026, 9, 12)
    cached_minutes([_session_minute(0, 100.0, 101.0, 99.0, 100.5, 1_000)])

    assert bars._todays_bar("NVDA", saturday) is None
