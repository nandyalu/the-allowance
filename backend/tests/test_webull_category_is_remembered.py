"""The Webull category is stored, not just memoized.

Webull's market-data calls need to know whether a ticker is a US_STOCK or a
US_ETF, and the app cannot know up front — it tries one, then the other. That
answer used to live only in a dict inside the process, so every restart threw
it away and every ticker paid an extra probe request to learn it again. On
2026-09-09 this app restarted 22 times while Webull was refusing 524 of its
calls for making too many; relearning a fact it already knew was part of it.
"""
import pytest

from backend.services import quotes


@pytest.fixture(autouse=True)
def cold_process(monkeypatch):
    """No memo, the way a freshly started container begins."""
    monkeypatch.setattr(quotes, "_category_cache", {})


def test_a_learned_category_is_written_to_the_database(isolated_ticker_status):
    quotes.remember_category("NVDA", "US_STOCK")

    assert isolated_ticker_status["NVDA"].webull_category == "US_STOCK"


def test_a_stored_category_survives_a_restart(isolated_ticker_status, monkeypatch):
    """The point of the whole change: a new process must not have to ask
    Webull again to learn something it already wrote down."""
    quotes.remember_category("NVDA", "US_STOCK")

    monkeypatch.setattr(quotes, "_category_cache", {})  # the restart

    assert quotes.category_for("NVDA") == "US_STOCK"


def test_an_unknown_ticker_has_no_category(isolated_ticker_status):
    """None is what sends the caller to probe US_STOCK and then US_ETF, so it
    has to stay distinguishable from a learned value."""
    assert quotes.category_for("NEVERSEEN") is None


def test_the_memo_answers_without_touching_the_database(isolated_ticker_status, monkeypatch):
    """A warm process must not pay a query per request."""
    quotes.remember_category("NVDA", "US_STOCK")
    monkeypatch.setattr(
        quotes_db(), "get_webull_category", lambda ticker: pytest.fail("read the database")
    )

    assert quotes.category_for("NVDA") == "US_STOCK"


def test_rewriting_the_same_category_does_not_write_again(isolated_ticker_status, monkeypatch):
    """Every successful request calls this, so the ordinary case has to be
    free."""
    quotes.remember_category("NVDA", "US_STOCK")
    monkeypatch.setattr(
        quotes_db(), "set_webull_category", lambda ticker, category: pytest.fail("wrote again")
    )

    quotes.remember_category("NVDA", "US_STOCK")


def test_a_changed_category_is_written_through(isolated_ticker_status):
    """A ticker that starts answering on the other category — a conversion, or
    a symbol reused — must not be pinned to the stale answer forever."""
    quotes.remember_category("SPY", "US_STOCK")
    quotes.remember_category("SPY", "US_ETF")

    assert quotes.category_for("SPY") == "US_ETF"
    assert isolated_ticker_status["SPY"].webull_category == "US_ETF"


def test_a_database_failure_does_not_cost_the_quote(isolated_ticker_status, monkeypatch):
    """This line used to be a dict assignment that could not fail. Now it
    reaches a database, and a caller asking for a price must not lose it
    because the app could not write down how the price was fetched."""
    def broken(ticker, category):
        raise RuntimeError("database is locked")

    monkeypatch.setattr(quotes_db(), "set_webull_category", broken)

    quotes.remember_category("NVDA", "US_STOCK")  # must not raise

    assert quotes.category_for("NVDA") == "US_STOCK"  # the memo still works


def test_an_unreadable_row_falls_back_to_probing(isolated_ticker_status, monkeypatch):
    def broken(ticker):
        raise RuntimeError("database is locked")

    monkeypatch.setattr(quotes_db(), "get_webull_category", broken)

    assert quotes.category_for("NVDA") is None  # probe both, rather than raise


def quotes_db():
    """The db module as quotes.category_for resolves it — imported lazily
    inside the function, so patching it means patching the module itself."""
    from backend.database import db

    return db
