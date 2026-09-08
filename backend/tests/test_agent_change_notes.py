"""The other half of a `note` order: telling the agent when one was answered.

A note reaches the maintainers and "nothing acts on it automatically" — until
this existed, that was also true of the maintainers' side. If someone built
what a note asked for, the agent had no way to learn its note had been read,
and would keep asking or keep working around a restriction that no longer
existed.

Built 2026-09-08 as a database-backed setting, then rebuilt the same day as a
git-tracked file (backend/agent_changes.json) instead — this project has
reset its own database more than once, and an entry here should survive that
the way JOURNEY.md already does. Edited by hand, in the same commit as the
change it describes.
"""
import datetime
import json

import pytest

from backend.services import agent, agent_book


def _book():
    return agent_book.Book(budget=10_000.0, cash=1_000.0, realized_pnl=0.0, holdings=[])


def _days_ago(n):
    return (datetime.date.today() - datetime.timedelta(days=n)).isoformat()


# --- reading backend/agent_changes.json -----------------------------------------


@pytest.fixture
def changes_file(tmp_path, monkeypatch):
    """A throwaway file standing in for backend/agent_changes.json, so no test
    touches the real one."""
    path = tmp_path / "agent_changes.json"
    monkeypatch.setattr(agent, "_CHANGES_FILE", path)
    return path


def test_a_missing_file_is_not_an_error(changes_file):
    """A fresh checkout with no file yet must not crash the agent's first
    decision pass."""
    assert agent.load_change_notes() == []


def test_a_written_entry_comes_back(changes_file):
    changes_file.write_text(json.dumps([
        {"date": "2026-09-08", "message": "You can now see settled vs. unsettled cash."},
    ]))

    got = agent.load_change_notes()

    assert got == [{"date": "2026-09-08", "message": "You can now see settled vs. unsettled cash."}]


def test_unreadable_json_does_not_crash_a_decision_pass(changes_file):
    """A typo while hand-editing the file must degrade to nothing shown, not
    take the agent down with it. The startup log is what catches this, not an
    exception mid-pass."""
    changes_file.write_text("{not valid json")

    assert agent.load_change_notes() == []


def test_the_file_must_be_a_list(changes_file):
    changes_file.write_text(json.dumps({"date": "2026-09-08", "message": "wrong shape"}))

    assert agent.load_change_notes() == []


def test_an_entry_missing_a_field_is_dropped_not_fatal(changes_file):
    changes_file.write_text(json.dumps([
        {"date": "2026-09-08"},
        {"message": "no date"},
        {"date": "2026-09-07", "message": "this one is fine"},
    ]))

    got = agent.load_change_notes()

    assert got == [{"date": "2026-09-07", "message": "this one is fine"}]


# --- the window: _recent_changes -------------------------------------------------


def test_a_note_from_today_is_shown(changes_file):
    changes_file.write_text(json.dumps([{"date": _days_ago(0), "message": "fresh"}]))

    assert [c["message"] for c in agent._recent_changes()] == ["fresh"]


def test_a_note_from_ten_days_ago_is_not_shown(changes_file):
    """_CHANGE_NOTES_WINDOW_DAYS is 3 — this is well outside it."""
    changes_file.write_text(json.dumps([{"date": _days_ago(10), "message": "old news"}]))

    assert agent._recent_changes() == []


def test_notes_come_back_oldest_first(changes_file):
    changes_file.write_text(json.dumps([
        {"date": _days_ago(1), "message": "second"},
        {"date": _days_ago(2), "message": "first"},
    ]))

    assert [c["message"] for c in agent._recent_changes()] == ["first", "second"]


def test_an_unparseable_date_is_dropped_not_fatal(changes_file):
    changes_file.write_text(json.dumps([
        {"date": "not-a-date", "message": "bad"},
        {"date": _days_ago(0), "message": "good"},
    ]))

    assert [c["message"] for c in agent._recent_changes()] == ["good"]


# --- the prompt: describe_recent_changes / build_prompt -------------------------


def test_no_changes_means_no_section():
    assert agent.describe_recent_changes([]) == []


def test_a_change_is_dated_and_stated():
    said = "\n".join(agent.describe_recent_changes(
        [{"date": "2026-09-08", "message": "You can now sell into a resting exit."}]
    ))

    assert "2026-09-08" in said
    assert "You can now sell into a resting exit." in said


def test_the_section_reaches_the_prompt():
    prompt = agent.build_prompt(
        _book(), [], {},
        changes=[{"date": "2026-09-08", "message": "New tool: X."}],
    )
    assert "New tool: X." in prompt


def test_no_changes_means_the_prompt_says_nothing_about_it():
    """The ordinary case. A header with nothing under it is prompt the agent
    has to read past for no reason."""
    assert "Changes made to this app" not in agent.build_prompt(_book(), [], {}, changes=[])


# --- the checked-in file itself ---------------------------------------------------


def test_the_real_file_is_valid():
    """A guard against committing a typo in backend/agent_changes.json — the
    one file in this feature that is not a fixture."""
    entries = json.loads(agent._CHANGES_FILE.read_text())
    assert isinstance(entries, list)
    for entry in entries:
        assert set(entry) >= {"date", "message"}
        datetime.date.fromisoformat(entry["date"])  # raises if unparseable
