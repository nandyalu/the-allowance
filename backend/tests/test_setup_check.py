"""The first-run page, and the one property it must never lose.

Everything this app needs was configured through environment variables found
by reading documentation, and everything that went wrong said so only in a log
line nobody was watching. A container came up healthy, placed no orders, and
the reason was one `docker logs` away.

**The security property under test: this reports whether something is
configured and never what it is configured to.** ``snapshot_export.py`` writes
the settings payload to a file pushed to Cloudflare Pages, so a field that can
carry a secret is a field that can publish one.
"""
import pytest

from backend.services import setup_check

SECRETS = {
    "WEBULL_APP_KEY": "wb-key-do-not-leak",
    "WEBULL_APP_SECRET": "wb-secret-do-not-leak",
    "WEBULL_ACCOUNT_ID": "DEL546C9",
    "OPENAI_COMPATIBLE_API_KEY": "csk-do-not-leak",
    "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/do-not-leak",
    "FRED_API_KEY": "fred-do-not-leak",
}


@pytest.fixture
def fully_configured(monkeypatch):
    for name, value in SECRETS.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setenv("WEBULL_SANDBOX", "1")
    monkeypatch.setattr(setup_check.analysis, "list_models", lambda: ["a-model"])
    monkeypatch.setattr(setup_check.agent, "is_enabled", lambda: True)
    monkeypatch.setattr(setup_check.db, "get_setting", lambda key: "on")


@pytest.fixture
def nothing_configured(monkeypatch):
    for name in [*SECRETS, "WEBULL_SANDBOX"]:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(setup_check.analysis, "list_models", lambda: [])
    monkeypatch.setattr(setup_check.agent, "is_enabled", lambda: False)
    monkeypatch.setattr(setup_check.db, "get_setting", lambda key: None)


# --- the property that matters --------------------------------------------------


def test_no_configured_value_appears_anywhere_in_the_payload(fully_configured):
    """The whole security design. Every secret is set to a recognisable
    string; none of them may appear in the response, in any field, at any
    depth."""
    import json

    payload = json.dumps(setup_check.status())

    for value in SECRETS.values():
        assert value not in payload


def test_the_account_number_is_not_echoed_back(fully_configured):
    """Even the account id — which is an identifier rather than a credential —
    stays out. The example in `fix` is a placeholder, and it is only shown
    while the real one is missing."""
    import json

    assert "DEL546C9" not in json.dumps(setup_check.status())


def test_the_example_lines_are_shown_only_while_something_is_missing(nothing_configured):
    """A `fix` is teaching material, so it disappears once the thing is set —
    otherwise the page reads like an instruction to change what already works."""
    checks = {c["key"]: c for c in setup_check.status()["checks"]}

    assert "WEBULL_APP_KEY" in checks["webull_credentials"]["fix"]
    assert checks["webull_credentials"]["ready"] is False


def test_a_satisfied_check_offers_no_fix(fully_configured):
    checks = {c["key"]: c for c in setup_check.status()["checks"]}

    assert checks["webull_credentials"]["ready"] is True
    assert checks["webull_credentials"]["fix"] == ""


# --- what it reports ------------------------------------------------------------


def test_a_fully_configured_deployment_is_ready(fully_configured):
    assert setup_check.status()["ready"] is True


def test_a_bare_deployment_is_not_ready(nothing_configured):
    status = setup_check.status()

    assert status["ready"] is False
    assert status["first_run"] is True


def test_the_optional_ones_do_not_block(monkeypatch, fully_configured):
    """Discord and FRED are worth having and must never stop a deployment."""
    monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)
    monkeypatch.delenv("FRED_API_KEY", raising=False)

    status = setup_check.status()
    checks = {c["key"]: c for c in status["checks"]}

    assert checks["discord"]["ready"] is False
    assert checks["fred"]["ready"] is False
    assert checks["discord"]["blocking"] is False
    assert status["ready"] is True


def test_an_unreachable_model_endpoint_blocks(monkeypatch, fully_configured):
    """"The variable is set" and "the endpoint answers" are different facts,
    and only the second lets an analysis run."""
    monkeypatch.setattr(setup_check.analysis, "list_models", lambda: [])

    checks = {c["key"]: c for c in setup_check.status()["checks"]}
    assert checks["llm"]["ready"] is False
    assert setup_check.status()["ready"] is False


def test_an_endpoint_that_raises_is_reported_not_propagated(monkeypatch, fully_configured):
    """A setup page that 500s while explaining why nothing works is worse than
    the log line it replaces."""
    def boom():
        raise RuntimeError("connection refused")

    monkeypatch.setattr(setup_check.analysis, "list_models", boom)

    checks = {c["key"]: c for c in setup_check.status()["checks"]}
    assert checks["llm"]["ready"] is False


def test_the_sandbox_guard_is_reported_but_still_enforced_in_code(monkeypatch, fully_configured):
    """The page reports the guard; it does not become the guard. Every order
    still calls _assert_sandbox() regardless of what this says."""
    monkeypatch.delenv("WEBULL_SANDBOX", raising=False)

    checks = {c["key"]: c for c in setup_check.status()["checks"]}
    assert checks["sandbox"]["ready"] is False
    assert checks["sandbox"]["blocking"] is True


def test_first_run_is_false_once_the_agent_has_ever_been_switched_on(monkeypatch, fully_configured):
    """It decides whether the page interrupts or waits to be visited, so it
    must mean 'never started', not 'currently off'."""
    monkeypatch.setattr(setup_check.agent, "is_enabled", lambda: False)
    monkeypatch.setattr(setup_check.db, "get_setting", lambda key: "off")

    status = setup_check.status()
    assert status["first_run"] is False
    assert status["ready"] is False  # still not ready — the agent is off


def test_blocking_checks_come_first(fully_configured):
    """The order a person fixes them in."""
    checks = setup_check.status()["checks"]
    blocking = [c["blocking"] for c in checks]

    assert blocking == sorted(blocking, reverse=True)


def test_it_works_before_the_migrations_have_run(monkeypatch, nothing_configured):
    """The case this page exists for. A container whose migrations have not
    run has no botsetting table, and a setup page that 500s while explaining
    why nothing works is worse than the log line it replaces. Caught by
    running the built image with no database at all."""
    def no_table(key):
        raise RuntimeError("no such table: botsetting")

    monkeypatch.setattr(setup_check.db, "get_setting", no_table)

    status = setup_check.status()

    assert status["ready"] is False
    assert status["first_run"] is True
    assert len(status["checks"]) == 7


# --- the two kinds of fix -------------------------------------------------------


def test_the_agent_check_links_into_the_app_rather_than_describing_a_page(nothing_configured):
    """Everything else is fixed in the environment; this one is fixed in the
    app. Telling somebody to 'turn it on from the settings page' is the
    behaviour this whole feature exists to end — and rendered in the `fix`
    field it would appear inside a code block, reading as something to paste."""
    checks = {c["key"]: c for c in setup_check.status()["checks"]}
    agent_check = checks["agent_enabled"]

    assert agent_check["action_path"] == "/settings"
    assert agent_check["action_label"]
    assert agent_check["fix"] == ""


def test_environment_requirements_offer_no_in_app_action(nothing_configured):
    """A link to a page that cannot fix the problem is worse than no link."""
    checks = {c["key"]: c for c in setup_check.status()["checks"]}

    for key in ("webull_credentials", "sandbox", "account", "llm"):
        assert checks[key]["action_path"] == "", key
        assert checks[key]["fix"], key


def test_a_satisfied_check_offers_neither(fully_configured):
    checks = {c["key"]: c for c in setup_check.status()["checks"]}

    assert checks["agent_enabled"]["action_path"] == ""
    assert checks["agent_enabled"]["fix"] == ""
