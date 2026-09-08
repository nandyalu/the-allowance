"""Backfill 1-minute intraday bars for every tracked ticker, back to the
experiment's start (backend/services/intraday.EXPERIMENT_START).

Run once, by hand, after the intraday cache first ships — the watchdog's own
15-minute tick (backend/services/watchdog.py) keeps it current from then on,
the same way it already does for TickerPrice, but it only ever asks for a
short recent window and was never meant to reach back to day one.

Safe to run again later: backfill() upserts, so re-running over an
already-covered range costs only the wasted API calls.

    python -m backend.scripts.backfill_intraday_bars
    python -m backend.scripts.backfill_intraday_bars --ticker AVGO --ticker OLDCO
    python -m backend.scripts.backfill_intraday_bars --since 2026-09-05
"""
import argparse
import datetime

from backend.database import db
from backend.services import intraday


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ticker", action="append", dest="tickers",
        help="back-fill only this ticker (repeatable) instead of the whole watchlist — "
        "use this for a ticker no longer tracked but still worth a historical chart",
    )
    parser.add_argument(
        "--since", type=datetime.date.fromisoformat, default=None,
        help="how far back to page (YYYY-MM-DD). Defaults to the experiment's start.",
    )
    args = parser.parse_args()

    tickers = args.tickers or sorted(db.get_watchlist())
    if not tickers:
        print("No tickers to back-fill — the watchlist is empty and none were named with --ticker.")
        return 0

    since = (
        datetime.datetime.combine(args.since, datetime.time.min)
        if args.since else intraday.EXPERIMENT_START
    )

    total = 0
    for ticker in tickers:
        written = intraday.backfill(ticker, since=since)
        print(f"  {ticker}: {written} bar(s)")
        total += written

    print()
    print(f"{total} bar(s) written across {len(tickers)} ticker(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
