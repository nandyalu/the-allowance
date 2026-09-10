"""The deployment names the account it owns, and refuses to trade otherwise.

Added 2026-09-09, when a second container was about to run. The three older
guards narrow the sandbox's five accounts to "an INDIVIDUAL_CASH account
numbered DE…" — one account, and the *same* one account for every deployment
applying the same rule. Two containers sharing a book leaves a record that
cannot say which of them placed an order.

The property every test here defends: this guard only ever narrows. An account
must be simulated, of the right class, *and* the one that was named. Nothing
in it can reach an account the older three would have refused.
"""
import pytest

from backend.services import sandbox_broker


def _account(number="DEL546C9", account_id="123456", account_class="INDIVIDUAL_CASH"):
    return {
        "account_number": number,
        "account_id": account_id,
        "account_class": account_class,
    }


@pytest.fixture(autouse=True)
def sandbox_with_no_cache(monkeypatch):
    """A sandbox client, an empty account cache, and no ambient config — each
    test states the configuration it is testing."""
    monkeypatch.setattr(sandbox_broker, "_account_id", None)
    monkeypatch.setattr(sandbox_broker.quotes, "is_sandbox", lambda: True)
    monkeypatch.delenv("WEBULL_ACCOUNT_ID", raising=False)
    monkeypatch.delenv("WEBULL_ACCOUNT_CLASS", raising=False)


@pytest.fixture
def accounts(monkeypatch):
    """Stand in for the account list Webull returns."""
    def set_accounts(rows):
        monkeypatch.setattr(sandbox_broker.quotes, "get_api_client", lambda: object())
        monkeypatch.setattr(sandbox_broker, "_rows", lambda response: rows)

        class _AccountV2:
            def __init__(self, client):
                pass

            def get_account_list(self):
                return rows

        import webull.trade.trade.v2.account_info_v2 as module
        monkeypatch.setattr(module, "AccountV2", _AccountV2)

    return set_accounts


# --- the variable itself --------------------------------------------------------


def test_an_unset_variable_is_an_error_not_a_default():
    """A default would defeat the point. The value is that a person wrote down
    which book this container owns."""
    with pytest.raises(sandbox_broker.NoAccountConfiguredError):
        sandbox_broker.configured_account()


def test_an_empty_variable_is_the_same_as_unset(monkeypatch):
    monkeypatch.setenv("WEBULL_ACCOUNT_ID", "   ")
    with pytest.raises(sandbox_broker.NoAccountConfiguredError):
        sandbox_broker.configured_account()


def test_a_set_variable_is_read_and_trimmed(monkeypatch):
    monkeypatch.setenv("WEBULL_ACCOUNT_ID", "  DEL546C9 ")
    assert sandbox_broker.configured_account() == "DEL546C9"


# --- resolving an account -------------------------------------------------------


def test_nothing_is_traded_when_no_account_is_named(accounts, caplog):
    """The whole point: switched on, and doing nothing, loudly."""
    accounts([_account()])

    assert sandbox_broker.get_paper_account_id() is None
    assert "WEBULL_ACCOUNT_ID is not set" in caplog.text


def test_the_named_account_is_used(accounts, monkeypatch):
    monkeypatch.setenv("WEBULL_ACCOUNT_ID", "DEL546C9")
    accounts([_account(number="DEL546C9", account_id="123456")])

    assert sandbox_broker.get_paper_account_id() == "123456"


def test_the_internal_id_is_accepted_too(accounts, monkeypatch):
    """Whichever identifier the operator pasted. The two are different shapes,
    so accepting either cannot make a wrong value look right."""
    monkeypatch.setenv("WEBULL_ACCOUNT_ID", "123456")
    accounts([_account(number="DEL546C9", account_id="123456")])

    assert sandbox_broker.get_paper_account_id() == "123456"


def test_a_valid_account_that_was_not_named_is_refused(accounts, monkeypatch, caplog):
    """This is the case the guard exists for: a real, simulated, correctly
    classed account that belongs to the *other* container."""
    monkeypatch.setenv("WEBULL_ACCOUNT_ID", "DEL999X9")
    accounts([_account(number="DEL546C9", account_id="123456")])

    assert sandbox_broker.get_paper_account_id() is None
    assert "No INDIVIDUAL_CASH account matching WEBULL_ACCOUNT_ID=DEL999X9" in caplog.text


def test_a_wrong_value_matches_nothing_and_refuses(accounts, monkeypatch):
    """A typo fails closed rather than selecting something else."""
    monkeypatch.setenv("WEBULL_ACCOUNT_ID", "DEL546C8")  # one character out
    accounts([_account(number="DEL546C9", account_id="123456")])

    assert sandbox_broker.get_paper_account_id() is None


# --- it narrows, never widens ---------------------------------------------------


def test_naming_a_production_account_does_not_let_it_through(accounts, monkeypatch, caplog):
    """The DE-prefix check still runs first. Naming a non-simulated account
    must not be a way to reach one."""
    monkeypatch.setenv("WEBULL_ACCOUNT_ID", "US1234567")
    accounts([_account(number="US1234567", account_id="999")])

    assert sandbox_broker.get_paper_account_id() is None
    assert "not simulated" in caplog.text


def test_naming_an_account_of_the_wrong_class_does_not_let_it_through(accounts, monkeypatch):
    """The class check still runs. A named CRYPTO account is skipped like any
    other account of the wrong class."""
    monkeypatch.setenv("WEBULL_ACCOUNT_ID", "DEL744J6")
    accounts([_account(number="DEL744J6", account_id="777", account_class="CRYPTO")])

    assert sandbox_broker.get_paper_account_id() is None


def test_the_sandbox_flag_still_comes_first(accounts, monkeypatch):
    """Naming an account cannot substitute for WEBULL_SANDBOX. _assert_sandbox
    runs before any of this."""
    monkeypatch.setenv("WEBULL_ACCOUNT_ID", "DEL546C9")
    monkeypatch.setattr(sandbox_broker.quotes, "is_sandbox", lambda: False)
    accounts([_account()])

    with pytest.raises(sandbox_broker.NotSandboxError):
        sandbox_broker.get_paper_account_id()


def test_two_deployments_naming_different_accounts_resolve_differently(accounts, monkeypatch):
    """The reason this exists. Same rule, same account list, two containers —
    and each gets only its own book."""
    both = [
        _account(number="DEL546C9", account_id="111"),
        _account(number="DEM67245", account_id="222"),
    ]

    monkeypatch.setenv("WEBULL_ACCOUNT_ID", "DEL546C9")
    accounts(both)
    assert sandbox_broker.get_paper_account_id() == "111"

    monkeypatch.setattr(sandbox_broker, "_account_id", None)  # a second container
    monkeypatch.setenv("WEBULL_ACCOUNT_ID", "DEM67245")
    accounts(both)
    assert sandbox_broker.get_paper_account_id() == "222"
