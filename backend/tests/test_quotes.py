"""Unit tests for the pure parts of backend/services/quotes.py.

Split out of test_ask_quotes.py on 2026-09-10, when backend/services/ask.py
was deleted -- nothing had imported it since the Discord commands were
removed on 2026-09-01, and it still told the reader to "run /analyze first".
"""
from backend.services.quotes import extract_price


def test_extract_price_shapes():
    assert extract_price([{"symbol": "AAPL", "price": "333.26"}]) == 333.26
    assert extract_price({"snapshots": [{"last_price": 12.5}]}) == 12.5
    assert extract_price({"data": [{"close": "9.99"}]}) == 9.99
    assert extract_price({"symbol": "AAPL", "price": 101.0}) == 101.0  # bare dict


def test_extract_price_rejects_junk():
    assert extract_price([]) is None
    assert extract_price(None) is None
    assert extract_price([{"symbol": "AAPL"}]) is None
    assert extract_price([{"price": "not-a-number"}]) is None
    assert extract_price([{"price": 0}]) is None  # zero/negative quotes are unusable
    assert extract_price("weird") is None
