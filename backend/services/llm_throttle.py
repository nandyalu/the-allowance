"""Keep LLM calls inside whatever rate limit the vendor is enforcing.

The local GPU pool has no rate limit, so for most of this experiment's life
there was nothing to stay inside. A metered vendor is different: testing
Cerebras' free tier on 2026-09-09 returned a mix of 200s and 429s against both
its requests-per-minute and its tokens-per-minute ceilings, and the app had no
answer to either.

**Nothing here is guessed.** The first draft of this module invented an
exponential ladder — 5s, then 10, then 20 — and that would have been wrong in
a way that matters: the vendor asks for **58 seconds**, so six attempts on the
ladder would all have been spent inside the window the server was still
waiting out. Measured instead, on a deliberately tripped limit:

- Every **success** carries the full budget: ``x-ratelimit-remaining-requests-minute``
  and ``-tokens-minute`` (plus hour and day). So the app can know it is one
  call from the ceiling *before* it hits it.
- Every **429** carries ``retry-after`` in seconds, and a body naming the
  ceiling that was hit (``"Requests per minute limit exceeded"``,
  ``code: request_quota_exceeded``).

**A vendor that says none of this is left alone.** ollama returns no such
headers, so ``_remaining`` stays unknown and nothing ever waits — the local
path costs one dict lookup per call. That is the property to preserve in any
future edit: no delay may be introduced that a vendor did not ask for.

**One budget for the whole process.** The limit belongs to the account, not to
the run. Seven concurrent analyses share it, so a header read by one is a fact
about all seven. LangChain's own ``max_retries`` backs off per request, which
leaves seven analyses discovering the same ceiling seven times over while
keeping the endpoint saturated.
"""
import logging
import threading
import time

log = logging.getLogger("trading-experiment.llm_throttle")

# Attempts per call before the failure is handed back. Each wait is whatever
# the vendor asked for, so this is a count of refusals tolerated, not a ladder.
_ATTEMPTS = 4
# Used only when a 429 arrives with no retry-after to read.
_FALLBACK_WAIT_SECONDS = 30.0
# Below this many requests left in the current minute, wait for the window to
# roll rather than spend the last one and collect a 429. One, not zero: the
# header is read after the call that consumed it, and concurrent analyses are
# racing for the same budget.
_REQUEST_HEADROOM = 1
_WINDOW_SECONDS = 60.0

_lock = threading.Lock()
# What the vendor last told us, or None where it told us nothing.
_remaining_requests: int | None = None
_window_started_at = 0.0


def rate_limited(exc: Exception) -> bool:
    """Whether the vendor refused this call for being too fast, rather than
    for anything asking differently would fix."""
    if getattr(exc, "status_code", None) == 429:
        return True
    text = str(exc).lower()
    return "429" in text or "too many requests" in text or "rate limit" in text


def retry_after(exc: Exception) -> float | None:
    """The wait the vendor asked for, in seconds, or None if it did not say.

    Authoritative and always preferred over any number this app would pick:
    Cerebras asks for 58 seconds on a requests-per-minute refusal, which no
    reasonable backoff ladder would have landed on.
    """
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None) or {}
    value = headers.get("retry-after") or headers.get("Retry-After")
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def which_limit(exc: Exception) -> str:
    """Which ceiling the vendor says was hit, for the log — requests or tokens.

    Worth recording rather than flattening into "rate limited": a
    requests-per-minute refusal means slow down, a tokens-per-minute one means
    the prompts are too big for the pace, and those call for different fixes.
    """
    text = str(exc).lower()
    if "token" in text:
        return "tokens per minute"
    if "request" in text:
        return "requests per minute"
    return "an unnamed limit"


def _note_budget(headers) -> None:
    """Record what a successful response said is left in this minute."""
    global _remaining_requests, _window_started_at
    if not headers:
        return
    value = headers.get("x-ratelimit-remaining-requests-minute")
    if value is None:
        return  # a vendor that does not report, e.g. ollama — never throttled
    try:
        remaining = int(value)
    except (TypeError, ValueError):
        return
    with _lock:
        _remaining_requests = remaining
        if _window_started_at == 0.0 or remaining > (_remaining_requests or 0):
            _window_started_at = time.monotonic()


def _wait_for_the_window() -> None:
    """If the last response said the per-minute requests are nearly gone, wait
    for the window to roll instead of spending the last one on a refusal."""
    global _remaining_requests
    with _lock:
        if _remaining_requests is None or _remaining_requests > _REQUEST_HEADROOM:
            return
        elapsed = time.monotonic() - _window_started_at
        wait = max(0.0, _WINDOW_SECONDS - elapsed)
        # Assume the window rolled; the next response's header corrects us.
        _remaining_requests = None
    if wait > 0:
        log.info("Within one request of the per-minute ceiling — waiting %.0fs", wait)
        time.sleep(wait)


def current_budget() -> int | None:
    """Requests left in this minute as last reported, or None when the vendor
    reports nothing. Exported so a test and an operator can both read it."""
    return _remaining_requests


def reset() -> None:
    """Forget what any vendor reported. For tests, and for a provider switch:
    a budget learned from one vendor says nothing about another's."""
    global _remaining_requests, _window_started_at
    with _lock:
        _remaining_requests = None
        _window_started_at = 0.0


def throttled(call, raw_call=None):
    """Wrap one callable so it stays inside the vendor's limit and waits out a
    refusal for exactly as long as the vendor asked.

    ``raw_call`` is the same request with the HTTP response attached
    (``client.with_raw_response.create``). When given, it is used instead, so
    the budget headers can be read; the parsed object handed back is identical.
    Without it the call still works and simply learns nothing.

    Raises the vendor's own exception once the attempts are spent — losing an
    analysis is bad, but a silent wrong answer is worse, and the caller above
    records a failed run honestly. Anything that is not a rate limit is raised
    at once: a bad argument does not improve on a second attempt, and retrying
    one spends the budget this exists to protect.
    """
    def run(*args, **kwargs):
        for attempt in range(1, _ATTEMPTS + 1):
            _wait_for_the_window()
            try:
                if raw_call is not None:
                    raw = raw_call(*args, **kwargs)
                    _note_budget(getattr(raw, "headers", None))
                    return raw.parse()
                return call(*args, **kwargs)
            except Exception as exc:
                if not rate_limited(exc):
                    raise
                wait = retry_after(exc)
                if attempt == _ATTEMPTS:
                    log.warning(
                        "Vendor still refusing on %s after %d attempts — giving up",
                        which_limit(exc), attempt,
                    )
                    raise
                if wait is None:
                    wait = _FALLBACK_WAIT_SECONDS
                log.info(
                    "Vendor refused an LLM call on %s (attempt %d of %d) — "
                    "waiting the %.0fs it asked for",
                    which_limit(exc), attempt, _ATTEMPTS, wait,
                )
                reset()  # the budget we held is stale now
                time.sleep(wait)

    return run


def attach(*llms) -> None:
    """Put the throttle in front of every call these clients make.

    ``llm.client.create`` is the one method every LangChain path ends at, so
    wrapping it covers the whole graph — analysts, debate, trader — without
    touching the vendored submodule. Attaching to the client object rather
    than passing something per-call is the same reason the usage tracker and
    the trace recorder attach here: the stages share these two objects and
    none of them accepts an argument from the app.

    Idempotent: a client already wrapped is left alone, so building a graph
    twice cannot stack two throttles on one method.
    """
    for llm in llms:
        for name in ("client", "async_client"):
            client = getattr(llm, name, None)
            create = getattr(client, "create", None)
            if create is None or getattr(create, "_throttled", False):
                continue
            raw = getattr(getattr(client, "with_raw_response", None), "create", None)
            wrapped = throttled(create, raw)
            wrapped._throttled = True
            try:
                client.create = wrapped
            except Exception:
                # A client that refuses attribute assignment keeps working
                # unthrottled rather than failing the run.
                log.warning("Could not attach the throttle to %s", type(client).__name__)
