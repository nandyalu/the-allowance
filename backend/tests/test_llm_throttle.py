"""Staying inside whatever rate limit a vendor is enforcing.

Testing Cerebras' free tier on 2026-09-09 returned a mix of 200s and 429s
against both its requests-per-minute and tokens-per-minute ceilings, and the
app had no answer to either.

Nothing in the throttle is guessed, and these tests pin that. The first draft
invented an exponential ladder (5s, 10s, 20s) which would have been wrong in a
way that matters: the vendor asks for **58 seconds**, so every attempt on that
ladder would have been spent inside the window it was still waiting out.

The other load-bearing property is that this costs nothing on the local pool.
ollama reports no rate-limit headers and never returns 429, so no delay may
ever be introduced that a vendor did not ask for.
"""
import pytest

from backend.services import llm_throttle


@pytest.fixture(autouse=True)
def fresh_budget(monkeypatch):
    """The budget is process-wide by design, so one test's state would
    otherwise become the next test's starting point. Sleeping is patched out:
    the arithmetic is under test, not the wall clock."""
    llm_throttle.reset()
    monkeypatch.setattr(llm_throttle.time, "sleep", lambda seconds: None)
    yield
    llm_throttle.reset()


class _RateLimit(Exception):
    """A real Cerebras refusal, headers and body as measured."""

    def __init__(self, message="Requests per minute limit exceeded - too many requests sent.",
                 retry_after="58"):
        super().__init__(message)
        headers = {"retry-after": retry_after} if retry_after is not None else {}
        self.response = type("Response", (), {"headers": headers})()
        self.status_code = 429


class _Raw:
    """What ``with_raw_response.create`` hands back: the HTTP response, with
    the parsed object one call away."""

    def __init__(self, remaining="4", answer="answer"):
        self.headers = ({"x-ratelimit-remaining-requests-minute": remaining}
                        if remaining is not None else {})
        self._answer = answer

    def parse(self):
        return self._answer


# --- reading what the vendor said ----------------------------------------------


def test_a_rate_limit_is_recognised():
    assert llm_throttle.rate_limited(_RateLimit()) is True
    assert llm_throttle.rate_limited(Exception("Error code: 429")) is True
    assert llm_throttle.rate_limited(Exception("rate limit exceeded")) is True


def test_an_unrelated_error_is_not_a_rate_limit():
    assert llm_throttle.rate_limited(Exception("invalid model")) is False
    assert llm_throttle.rate_limited(Exception("context length exceeded")) is False


def test_the_retry_after_header_is_read():
    """58 seconds is what Cerebras actually asks for. Any ladder this app
    invented would have retried inside that window and failed."""
    assert llm_throttle.retry_after(_RateLimit()) == 58.0


def test_a_refusal_with_no_retry_after_says_so():
    assert llm_throttle.retry_after(_RateLimit(retry_after=None)) is None
    assert llm_throttle.retry_after(Exception("no response attached")) is None


def test_which_limit_was_hit_is_named():
    """A requests-per-minute refusal means slow down; a tokens-per-minute one
    means the prompts are too big for the pace. Different fixes."""
    assert llm_throttle.which_limit(_RateLimit()) == "requests per minute"
    assert llm_throttle.which_limit(
        _RateLimit("Tokens per minute limit exceeded")) == "tokens per minute"
    assert llm_throttle.which_limit(Exception("429")) == "an unnamed limit"


# --- the local pool pays nothing -----------------------------------------------


def test_a_vendor_that_reports_nothing_is_never_throttled():
    """ollama sends no rate-limit headers. Nothing may wait on its account."""
    calls = []
    run = llm_throttle.throttled(lambda **kw: calls.append(1) or "ok")

    for _ in range(10):
        assert run(model="x") == "ok"

    assert len(calls) == 10
    assert llm_throttle.current_budget() is None  # nothing learned, nothing waited


def test_headers_without_the_budget_field_teach_nothing():
    run = llm_throttle.throttled(lambda **kw: "unused", lambda **kw: _Raw(remaining=None))

    assert run(model="x") == "answer"
    assert llm_throttle.current_budget() is None


# --- learning the budget from a success ----------------------------------------


def test_the_remaining_budget_is_read_from_a_successful_call():
    run = llm_throttle.throttled(lambda **kw: "unused", lambda **kw: _Raw(remaining="4"))

    assert run(model="x") == "answer"
    assert llm_throttle.current_budget() == 4


def test_the_parsed_object_is_what_the_caller_gets():
    """Reading headers must not change what every caller above already
    expects back from client.create."""
    run = llm_throttle.throttled(lambda **kw: "unused",
                                 lambda **kw: _Raw(answer="the ChatCompletion"))

    assert run(model="x") == "the ChatCompletion"


def test_the_last_request_of_a_minute_waits_for_the_window(monkeypatch):
    """Spending the final request just collects a 429. Wait for the window to
    roll instead — the header is read after the call that consumed it, and
    concurrent analyses race for the same budget."""
    waits = []
    monkeypatch.setattr(llm_throttle.time, "sleep", lambda s: waits.append(s))
    calls = []

    def raw(**kwargs):
        calls.append(1)
        return _Raw(remaining="1" if len(calls) == 1 else "4")

    run = llm_throttle.throttled(lambda **kw: "unused", raw)
    run(model="x")          # learns only 1 left
    assert llm_throttle.current_budget() == 1
    run(model="x")          # must wait for the window before spending it

    assert waits and waits[0] > 0


# --- reacting to a refusal ------------------------------------------------------


def test_a_refusal_waits_exactly_as_long_as_the_vendor_asked(monkeypatch):
    waits = []
    monkeypatch.setattr(llm_throttle.time, "sleep", lambda s: waits.append(s))
    calls = []

    def busy_once(**kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise _RateLimit()
        return "ok"

    assert llm_throttle.throttled(busy_once)(model="x") == "ok"
    assert waits == [58.0]


def test_a_refusal_with_no_retry_after_falls_back_to_a_stated_wait(monkeypatch):
    waits = []
    monkeypatch.setattr(llm_throttle.time, "sleep", lambda s: waits.append(s))
    calls = []

    def busy_once(**kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise _RateLimit(retry_after=None)
        return "ok"

    llm_throttle.throttled(busy_once)(model="x")
    assert waits == [llm_throttle._FALLBACK_WAIT_SECONDS]


def test_it_gives_up_rather_than_retrying_forever():
    """An analysis lost to a wall of refusals is bad. One that hangs while the
    agent waits for it is worse."""
    calls = []

    def always_busy(**kwargs):
        calls.append(1)
        raise _RateLimit()

    with pytest.raises(_RateLimit):
        llm_throttle.throttled(always_busy)(model="x")

    assert len(calls) == llm_throttle._ATTEMPTS


def test_an_unrelated_error_is_raised_at_once():
    calls = []

    def broken(**kwargs):
        calls.append(1)
        raise ValueError("invalid model")

    with pytest.raises(ValueError):
        llm_throttle.throttled(broken)(model="x")

    assert len(calls) == 1


# --- attaching it ---------------------------------------------------------------


class _Client:
    def __init__(self):
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        return "answer"


class _Llm:
    def __init__(self):
        self.client = _Client()


def test_attaching_wraps_the_one_method_every_call_ends_at():
    llm = _Llm()
    llm_throttle.attach(llm)

    assert llm.client.create(model="x") == "answer"
    assert llm.client.calls == 1


def test_attaching_twice_does_not_stack_two_throttles():
    """_build_graph runs per analysis and the decision pass attaches again on
    its own; neither may double-wrap a client."""
    llm = _Llm()
    llm_throttle.attach(llm)
    first = llm.client.create
    llm_throttle.attach(llm)

    assert llm.client.create is first


def test_a_client_that_cannot_be_wrapped_still_works():
    """Losing the throttle is survivable. Losing the run is not."""
    class _Frozen:
        __slots__ = ()

        def create(self, **kwargs):
            return "answer"

    class _Odd:
        client = _Frozen()

    llm = _Odd()
    llm_throttle.attach(llm)  # must not raise

    assert llm.client.create(model="x") == "answer"
