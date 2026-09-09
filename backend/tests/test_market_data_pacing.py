"""Pacing the Webull market-data endpoint.

On 2026-09-09 Webull refused 524 of this app's market-data calls — 332 quotes
and 192 daily-bar fetches — because the watchdog fired about twenty requests
in a six-second burst every fifteen minutes with nothing spacing them out.
Webull publishes no rate limit for these endpoints, so the numbers here come
from what actually failed rather than from a documented ceiling.

These tests call the real pacing functions with the real constants. The
autouse fixture in conftest.py that no-ops the sleep everywhere else is
deliberately undone in the ones that need it.
"""
import time

import pytest

from backend.services import quotes

# Captured at import, which happens before conftest's autouse fixture replaces
# it with a no-op. The test that measures a real gap puts this back.
_REAL_CLAIM_A_SLOT = quotes._claim_a_slot


@pytest.fixture(autouse=True)
def fresh_pace(monkeypatch):
    """Each test starts at the floor with no request behind it. The pace is a
    module global, so without this one test's backoff would set the next
    one's starting point."""
    monkeypatch.setattr(quotes, "_pace_seconds", quotes._PACE_FLOOR_SECONDS)
    monkeypatch.setattr(quotes, "_last_request_at", 0.0)


class _RateLimit(Exception):
    def __str__(self):
        return "HTTP Status: 429, Code: TOO_MANY_REQUESTS, Msg: Too many requests"


# --- recognising the refusal ---------------------------------------------------


@pytest.mark.parametrize(
    "message",
    [
        "HTTP Status: 429, Code: TOO_MANY_REQUESTS, Msg: Too many requests",
        "too many requests",
        "Code: TOO_MANY_REQUESTS",
    ],
)
def test_a_rate_limit_is_recognised(message):
    assert quotes.rate_limited(Exception(message)) is True


def test_an_unrelated_error_is_not_a_rate_limit():
    """Load-bearing: anything not a rate limit is raised immediately rather
    than retried, and still falls through to the next category."""
    assert quotes.rate_limited(Exception("invalid symbol")) is False
    assert quotes.rate_limited(Exception("unauthorized")) is False


# --- the retry budget ----------------------------------------------------------


def test_a_request_that_works_is_made_once(monkeypatch):
    monkeypatch.setattr(quotes, "_claim_a_slot", lambda: None)
    calls = []

    result = quotes.market_data_request(lambda: calls.append(1) or "ok", "a quote for AAA")

    assert result == "ok"
    assert len(calls) == 1


def test_a_rate_limited_request_is_retried_three_times_then_gives_up(monkeypatch):
    """Three attempts, then the vendor's own exception is raised — which is
    what sends the caller to yfinance."""
    monkeypatch.setattr(quotes, "_claim_a_slot", lambda: None)
    calls = []

    def always_busy():
        calls.append(1)
        raise _RateLimit()

    with pytest.raises(_RateLimit):
        quotes.market_data_request(always_busy, "a quote for AAA")

    assert len(calls) == quotes._MARKET_DATA_ATTEMPTS == 3


def test_a_retry_that_succeeds_returns_the_answer(monkeypatch):
    monkeypatch.setattr(quotes, "_claim_a_slot", lambda: None)
    calls = []

    def busy_once():
        calls.append(1)
        if len(calls) == 1:
            raise _RateLimit()
        return "ok"

    assert quotes.market_data_request(busy_once, "a quote for AAA") == "ok"
    assert len(calls) == 2


def test_an_unrelated_error_is_not_retried(monkeypatch):
    """Retrying a bad argument cannot help, and spends the quota this exists
    to protect."""
    monkeypatch.setattr(quotes, "_claim_a_slot", lambda: None)
    calls = []

    def broken():
        calls.append(1)
        raise ValueError("invalid symbol")

    with pytest.raises(ValueError):
        quotes.market_data_request(broken, "a quote for AAA")

    assert len(calls) == 1


# --- the pace itself -----------------------------------------------------------


def test_the_pace_widens_on_a_rate_limit_and_stops_at_the_ceiling(monkeypatch):
    monkeypatch.setattr(quotes, "_claim_a_slot", lambda: None)

    def always_busy():
        raise _RateLimit()

    with pytest.raises(_RateLimit):
        quotes.market_data_request(always_busy, "a quote for AAA")

    assert quotes._pace_seconds > quotes._PACE_FLOOR_SECONDS
    for _ in range(10):
        quotes._widen_pace()
    assert quotes._pace_seconds == quotes._PACE_CEILING_SECONDS


def test_the_pace_narrows_on_success_and_stops_at_the_floor():
    """Widen fast, narrow slowly — recovering in one step would let the next
    burst trip the limit again the moment one call succeeds."""
    quotes._widen_pace()
    widened = quotes._pace_seconds
    quotes._narrow_pace()
    assert quotes._pace_seconds < widened
    assert quotes._pace_seconds > quotes._PACE_FLOOR_SECONDS  # not all at once

    for _ in range(50):
        quotes._narrow_pace()
    assert quotes._pace_seconds == quotes._PACE_FLOOR_SECONDS


def test_the_floor_is_three_seconds_and_the_ceiling_is_ten():
    """Both numbers are in JOURNEY.md's 2026-09-09 entry. Changing one without
    the other leaves the record describing a system that no longer exists."""
    assert quotes._PACE_FLOOR_SECONDS == 3.0
    assert quotes._PACE_CEILING_SECONDS == 10.0


def test_two_requests_in_a_row_are_actually_spaced(monkeypatch):
    """The real sleep, with the constants shrunk — the arithmetic is what is
    under test, not the wall clock."""
    monkeypatch.setattr(quotes, "_claim_a_slot", _REAL_CLAIM_A_SLOT)
    monkeypatch.setattr(quotes, "_pace_seconds", 0.05)
    monkeypatch.setattr(quotes, "_last_request_at", 0.0)

    started = time.monotonic()
    quotes._claim_a_slot()  # first is free: nothing has gone before it
    quotes._claim_a_slot()  # second waits out the gap
    elapsed = time.monotonic() - started

    assert elapsed >= 0.05
