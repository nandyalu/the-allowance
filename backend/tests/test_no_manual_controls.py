"""The experiment's core rule, pinned so a contributor meets it on the commit
that breaks it rather than in a review.

**Since 2026-09-01 there are no manual controls anywhere.** No Discord slash
command, no button that adds a ticker, starts an analysis or places a trade.
The app had twenty-three commands and every one was removed.

The reason is the whole experiment: a control that lets a person nudge the
book puts a second decision-maker in the record, and afterwards nothing can
tell which one produced a result. A record with two authors is not evidence
about either.

**This was written down in four prose files and enforced by nothing.** Adding
a "run now" endpoint is an obvious, helpful-looking change for someone who has
not read them — and it is the one change that would quietly end the experiment
rather than adjust it.

The write surface is deliberately two routes. If you are here because this
test failed, the answer is almost never to add to the list: see CLAUDE.md,
"Since 2026-09-01 there are no manual controls anywhere".
"""
from backend.app import app

READ_METHODS = {"GET", "HEAD", "OPTIONS"}

# Every route that may change something, and why it is allowed to exist.
ALLOWED = {
    # Rests the stop and target the agent ALREADY chose, under shares it
    # already owns, for the case where the broker refused the bracket at
    # purchase. It decides nothing: it cannot pick a ticker, a size or a
    # level. That is what makes it a repair and not a control.
    ("POST", "/api/agent/exits/{ticker}"),
    # The experiment's own settings — the model, the budget, the research
    # price, and the switch that starts the agent. Changing one is a change to
    # the experiment and belongs in JOURNEY.md, but it is not a trade.
    ("PATCH", "/api/settings"),
}


def _write_routes() -> set[tuple[str, str]]:
    """Read from the OpenAPI schema rather than app.routes, because current
    FastAPI keeps included routers nested and app.routes reports none of
    them — a version detail that would have made this test silently vacuous."""
    spec = app.openapi()
    return {
        (method.upper(), path)
        for path, operations in spec["paths"].items()
        for method in operations
        if method.upper() not in READ_METHODS
    }


def test_the_write_surface_is_exactly_the_two_routes_that_decide_nothing():
    found = _write_routes()

    added = found - ALLOWED
    assert not added, (
        "A new write endpoint exists:\n  "
        + "\n  ".join(f"{m} {p}" for m, p in sorted(added))
        + "\n\nThis app has no manual controls on purpose. A control that lets a "
        "person nudge the book puts a second decision-maker in the record, and "
        "afterwards nothing can tell which one produced a result.\n\n"
        "If something needs correcting, the route is an entry in JOURNEY.md "
        "saying what and why, then a change made by hand. If this endpoint "
        "genuinely decides nothing — like the exits repair — add it to ALLOWED "
        "with a comment saying why it decides nothing."
    )

    removed = ALLOWED - found
    assert not removed, (
        "A documented write endpoint is gone:\n  "
        + "\n  ".join(f"{m} {p}" for m, p in sorted(removed))
        + "\n\nThat may well be right — but CLAUDE.md and docs/dashboard.md "
        "both describe this surface, so update them in the same change."
    )


def test_the_exits_route_is_the_only_way_to_reach_the_broker_from_the_api():
    """The narrower half of the rule. `POST /api/agent/exits/{ticker}` survives
    because it places the agent's own levels under the agent's own shares. A
    second broker-touching route would not have that property, and the failure
    above would read as a formality rather than as the rule it is."""
    broker_routes = {(m, p) for m, p in _write_routes() if "exits" in p or "order" in p}

    assert broker_routes == {("POST", "/api/agent/exits/{ticker}")}, (
        f"Routes that reach the broker: {sorted(broker_routes)}. "
        "Only the exits repair may, and it decides nothing."
    )
