"""The Journal page's month timeline — the same pattern as the Decisions
page's (test_agent_events_by_month.py), one level shallower: a journal
entry already is one calendar day, so there is no further day-vs-event
split to test here, only month grouping and filtering.

Every test monkeypatches journey.build rather than the database underneath
it — build() itself already has its own tests, and a fabricated day has no
more business landing in the real journal than a fabricated decision pass
does (see test_agent_events_by_month.py's own docstring)."""
import datetime

import pytest

from backend.services import journey
from backend.services.journey import Day


def _day(date: str, **over) -> Day:
    return Day(date=datetime.date.fromisoformat(date), **over)


@pytest.fixture
def fake_days(monkeypatch):
    def set_days(days: list[Day]):
        monkeypatch.setattr(journey, "build", lambda budget=None: days)

    return set_days


def test_months_come_back_newest_first(fake_days):
    fake_days([_day("2026-08-15"), _day("2026-09-01"), _day("2026-09-08")])

    assert journey.months_with_entries() == ["2026-09", "2026-08"]


def test_a_month_with_two_days_counts_once(fake_days):
    fake_days([_day("2026-09-01"), _day("2026-09-08")])

    assert journey.months_with_entries() == ["2026-09"]


def test_build_for_month_keeps_only_that_month(fake_days):
    august = _day("2026-08-30", reasoning="august day")
    september = _day("2026-09-01", reasoning="september day")
    fake_days([august, september])

    assert journey.build_for_month("2026-09") == [september]


def test_build_for_month_preserves_oldest_first_ordering(fake_days):
    first = _day("2026-09-01")
    second = _day("2026-09-08")
    fake_days([first, second])

    assert journey.build_for_month("2026-09") == [first, second]


def test_a_month_with_no_days_is_an_empty_list(fake_days):
    fake_days([_day("2026-09-01")])

    assert journey.build_for_month("2026-01") == []


def test_no_history_at_all_is_an_empty_list_of_months(fake_days):
    fake_days([])

    assert journey.months_with_entries() == []


# --- the routes the Journal page actually calls ----------------------------


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("PUBLIC_MODE", raising=False)
    from fastapi.testclient import TestClient

    from backend.app import app

    return TestClient(app)


def test_the_months_route_lists_every_month_newest_first(client, fake_days):
    fake_days([_day("2026-08-15"), _day("2026-09-01")])

    response = client.get("/api/agent/journey/entries/months")

    assert response.status_code == 200
    assert response.json() == ["2026-09", "2026-08"]


def test_the_entries_route_with_a_month_returns_only_that_month(client, fake_days):
    fake_days([_day("2026-08-30"), _day("2026-09-01")])

    response = client.get("/api/agent/journey/entries", params={"month": "2026-09"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["date"] == "2026-09-01"


def test_the_entries_route_without_a_month_keeps_the_old_recent_behaviour(client, monkeypatch):
    """Nothing on the frontend still calls this bare, but the route itself
    must keep working exactly as before — the new parameter is additive."""
    monkeypatch.setattr(journey, "build", lambda budget=None: [_day("2026-09-01")])

    response = client.get("/api/agent/journey/entries", params={"days": 5})

    assert response.status_code == 200
    assert len(response.json()) == 1
