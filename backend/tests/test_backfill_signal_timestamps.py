"""Recovering a signal's time of day from its trace_id.

Signal.trace_id, where it exists, is llm_traces.new_run_id()'s own output:
"<YYYYMMDDTHHMMSS>-<8 hex chars>" — the UTC instant the analysis started,
already sitting in the database as a string. Built 2026-09-08 alongside the
intraday bar cache, so a signal recorded before it had a created_at column
can still be placed on an intraday chart.
"""
from backend.scripts.backfill_signal_timestamps import timestamp_from_trace_id


def test_a_real_trace_id_parses_to_its_own_start_time():
    got = timestamp_from_trace_id("20260908T140150-a1b2c3d4")

    assert got.isoformat() == "2026-09-08T14:01:50"


def test_an_unreadable_stamp_returns_none_rather_than_raising():
    assert timestamp_from_trace_id("not-a-real-trace-id") is None


def test_an_empty_string_returns_none():
    assert timestamp_from_trace_id("") is None


def test_a_stamp_with_no_hex_suffix_still_parses():
    """split("-", 1) must not choke on a trace_id with no second segment —
    unlikely from new_run_id() itself, but worth being defensive about."""
    assert timestamp_from_trace_id("20260908T140150").isoformat() == "2026-09-08T14:01:50"
