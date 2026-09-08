"""The ticker-events API's bar shape carries a real timestamp, not just a date.

Added 2026-09-08 alongside the intraday bar cache — lightweight-charts needs
a genuine Unix timestamp to draw a bar at its true time of day; a
"YYYY-MM-DD" string only ever engages its daily/business-day mode.
"""
import datetime

from backend.api.routes.tickers import _ohlc_bar_out
from backend.services.intraday import ChartBar


def test_a_daily_bar_becomes_midnight_utc():
    bar = ChartBar(
        timestamp=datetime.datetime(2026, 9, 5), open=1, high=2, low=0.5, close=1.5, volume=100,
    )

    out = _ohlc_bar_out(bar)

    assert out.date == "2026-09-05"
    assert out.timestamp == int(
        datetime.datetime(2026, 9, 5, tzinfo=datetime.timezone.utc).timestamp()
    )


def test_an_intraday_bar_keeps_its_time_of_day():
    bar = ChartBar(
        timestamp=datetime.datetime(2026, 9, 8, 13, 35), open=1, high=2, low=0.5, close=1.5, volume=100,
    )

    out = _ohlc_bar_out(bar)

    assert out.date == "2026-09-08"
    assert out.timestamp == int(
        datetime.datetime(2026, 9, 8, 13, 35, tzinfo=datetime.timezone.utc).timestamp()
    )
