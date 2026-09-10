# The agent's journey — what we changed, and why

The app writes its own record: what it bought, what that cost, and what the agent said about it, day by day. Every sentence in it comes from a trade, a charge, or a decision pass, so it cannot drift from the book.

Read it at `/api/agent/journey`, or as files: one per month, under a folder per year, in the data volume beside the database and the logs.

```
data/journey/2026/08-August.md
data/journey/2026/09-September.md
```

The app rewrites them after grading each evening. `python -m backend.scripts.write_journey` regenerates them on demand.

Each file opens with the month in four numbers: positions opened, positions closed, research spent, and where the book started and finished. That way a file reads on its own, not only as part of a series. That is what makes them publishable later: a month is a post.

**The app generates them, and rewriting them is how they stay true.** Do not edit them. The next write discards the edit. Put commentary here instead.

**This file is the other half, and it is the half the app cannot write.** It knows the agent changed its mind. It does not know that we changed the prompt the week before, or added a research charge, or settled the debate-round count by running an experiment.

Without those causes, a month of record is a list of events nobody can learn from.

Two rules, both learned the hard way elsewhere in this project:

- **Write it when it happens, not afterwards.** A reason you reconstruct two weeks later is a story about what you would like to have been thinking.
- **Record what was wrong, not only what worked.** The entries that say "this turned out to be noise" are worth more than the ones that say "this worked". They are what stops someone proposing the same idea again in three weeks.


---

## The changelog: every change to the agent, and why

The entries below record what changed in the agent's behaviour and the reason for it. They moved here from `CLAUDE.md` on 2026-09-01, which had been keeping a second copy of the same thing.

**This file covers one agent: the merged agent that has run since 2026-09-01.** Before that date, two deployments ran side by side on the same code and different settings — a live bot on a fixed watchlist, and a separate analyst experiment that chose its own tickers. Both ended on 2026-09-01 and merged into the agent below. Their own history moved to two pages of its own, so this file stays about the agent that is actually running: [the two-book experiment](https://github.com/nandyalu/the-allowance/blob/main/docs/two-book-experiment.md) covers the live bot, and [the analyst experiment](https://github.com/nandyalu/the-allowance/blob/main/docs/analyst-experiment.md) covers the deployment that became this one.

`CLAUDE.md` now describes what the rules are. This describes how they got that way. Add an entry here **before** changing a rule, not after.

Newest first.

**2026-09-09 — the model dropdown works on a metered endpoint, and the reason it did not is worth writing down.** The second container logged `Couldn't list models from https://api.cerebras.ai/v1/models: HTTP Error 403: Forbidden`, so its settings page fell back to a free-text field. Two separate faults, and only one of them was the obvious one.

**The call sent no key.** The local pool needs none and has never been asked for one, so `list_models` was written without an `Authorization` header at all. Every metered provider wants one. That took a minute to find and a minute to fix.

**The call also looked like a robot, and that is the one that costs an hour.** With the key added it still returned 403. The key was not the problem: the *identical* request returns 403 sent as urllib and 200 sent as curl. Cerebras sits behind Cloudflare, urllib announces itself as `Python-urllib/3.14`, and Cloudflare refuses that outright. Nothing in the error says so — a 403 with a valid key reads as an authentication problem, and every instinct sends you back to the key.

Recorded because the next person to point this app at a new vendor will hit it, and because it is a general fact about this codebase rather than about Cerebras: anything here that reaches a third-party endpoint through `urllib` rather than through an SDK is one Cloudflare rule away from the same dead end.

**2026-09-09 — the model's reasoning is kept, after being generated, paid for and thrown away since the day the agent started.** Found by replaying a real stored prompt to check the new token counts: the pass reported 1,850 output tokens against a 758-character answer. That is 0.4 characters per token, which is not possible for returned text — so roughly nine tenths of what the model produced was going somewhere other than the record.

**It was reasoning, and the endpoint had been returning it all along.** Ollama's `/v1/chat/completions` puts it in a `reasoning` field beside the content — 5,336 characters of it against a 356-character answer on the replay that settled this. `ChatOpenAI` discards it deliberately, and says so: it "targets the official OpenAI specification" and does not extract "non-standard response fields added by third-party providers". There is no flag to keep it.

**So `_invoke` goes through the OpenAI client LangChain already built rather than `llm.invoke`.** That inherits the base URL, the key and the timeouts configured once, instead of standing up a second way to reach the model, and the raw response still carries the field. **It falls back to `llm.invoke` for any client that does not work this way** — Anthropic and Google go through their own packages, and switching provider is a config change this app supports. Losing the reasoning on another provider is acceptable; losing the pass would not be.

**This is the most useful thing on the page and it was the one thing missing.** The record held what the agent decided and, since 2026-09-01, the exact words it was asked. It never held *why*. The stored one-line `reasoning` is the model's own summary of its answer, written after the fact and in its own interest; this is the working-out — the moment it reads $0.94 of cash, weighs AVGO's resting target against the close, and talks itself into holding. A month of "Hold, cash too low" rows says nothing. A month of these says whether the reasoning behind them was any good.

**Stored NULL for every pass before today**, and nothing is backfilled: the text was never written down, and re-running an old prompt now would answer a different day's question with different prices.

**2026-09-09 — a decision pass now records what it cost, which nothing had ever counted.** Asked a plain question — how many tokens did the last pass use — and found the answer was nowhere. `agentrun` had eighteen columns and not one of them was a token count. It stored the prompt and the answer in full, and nothing about what they cost.

**The gap has the same cause as the one closed on 2026-09-01, and half of it was left open.** `llm_usage.UsageTracker` attaches to the graph's two LLM client objects, and the agent's `_ask` does not go through the graph — it calls a client no tracker is bound to. That is exactly why the prompt and response were missing until 2026-09-01, when they were added by hand. The tokens were the half nobody came back for. `Signal` has carried prompt tokens, completion tokens, calls and duration for an analysis since the cost telemetry landed; the pass that decides what to *do* with those analyses carried none of it.

**It is worth having because the number moves and the record could not see it.** Adding the sell-any-time rule earlier today made the prompt 459 characters longer, and the agent wakes several times a day rather than once — so prompt size is a recurring cost, and it is the number that would settle any question about moving to a paid vendor, where input and output are priced separately and eight times apart.

**Three columns: `prompt_tokens`, `completion_tokens`, `seconds`**, summed across the retry when there is one, because a retry is a second real call and its tokens are spent whether or not its answer is the one used. The seconds are the model calls' own wall clock rather than the whole pass, so the time and the tokens describe the same thing; a pass's total duration is a different number and is still not recorded. Counts come from the provider's `usage` block and are never estimated, for the reason that module already gives: an estimate is wrong by exactly the amount that matters once it is multiplied by a price per million. **Stored NULL, never 0, when nothing reported them** — a zero would read as a free call — and nothing is backfilled, because there is no honest way to recover a count after the fact.

**`_ask` returns a `str` subclass rather than a tuple, and that is a deliberate compromise.** A dozen callers and test fakes treat the answer as a plain string, several patching it with `lambda _p: "..."`; widening the return type would have broken all of them for three numbers one caller reads. As a `str` subclass it is still exactly the string it was, the counts ride along, and `_Spend.of` picks them off with `getattr` so a fake returning a bare string reports zero rather than raising.

**2026-09-09 — Webull had been rate-limiting most of this app's market-data calls all day, and nothing said so because everything fell back to yfinance.** Found while checking the logs after an unrelated redeploy. Today's log carries **332 refused quotes and 192 refused daily-bar fetches**; the persistent log goes back to 2026-09-03 and there were **none of either before 2026-09-08**. Every one of them returned `429 TOO_MANY_REQUESTS`.

**The cause is the Webull-first bar change from 2026-09-08, and the shape of it is worth stating exactly.** `bars._todays_bar` fetches the session in progress live on every call — correctly, since a bar that is still moving must never be cached. Before that change it fetched from yfinance. After it, it asks Webull first. The watchdog calls it once per tracked ticker every fifteen minutes, on the same tick that already asks Webull for that ticker's 1-minute bars, so each tick fired about twenty market-data requests in a six-second burst with no pacing at all. The failures land at :13:10, :28:10, :43:10 and :58:10 past the hour, which is the watchdog's own tick, and they start when the market opens rather than at a restart.

**The failure was also feeding itself.** Neither `quotes.get_realtime_price` nor `intraday.fetch_bars` knows whether a ticker is a stock or an ETF, so each tries `US_STOCK` and then `US_ETF` and remembers which answered — but only on success. A 429 says nothing about which category a ticker belongs to, and both functions treated it as if it did: the category was never learned, so the next tick paid for two requests instead of one. Being rate-limited doubled the traffic that caused the rate limiting. The cache is a plain in-memory dict as well, so all of it reset on each of the day's twenty-two restarts.

**Nothing broke, and that is exactly why it ran for a day unnoticed.** Both paths fall back to yfinance, so prices arrived and bars stayed correct. What was lost is the point of the change: during market hours it was making a doomed Webull call *and then* the yfinance call it was meant to avoid, which is strictly worse than either vendor alone.

**Three fixes, and the first removes the requests rather than spacing them out.** The app already holds what it was re-fetching: seven of ten tracked tickers had today's complete session in the 1-minute cache — 186 bars each, 13:30 through 16:35 — captured seconds earlier on the same watchdog tick. `_todays_bar` now builds the day's open, high, low, close and volume from those rows, and a bar summed from real minutes is better than a vendor's in-progress one, not merely cheaper. It falls back to a live fetch when the cache does not reach the session open, because a cache that starts at 11am would report 11am's price as the day's open — the three tickers with thin or missing coverage today would each have done exactly that, and their gaps were themselves caused by the 429s.

**Second, a 429 no longer costs a second category probe.** Both functions now ask whether the failure was a rate limit before deciding to try the other category: "too busy" is not evidence about whether a ticker is a stock or an ETF, so it stops the attempt outright. **Every other error still falls through as before**, and that limit is worth stating rather than tidying away — the first version of this change stopped on any exception at all, and an existing test caught it, because a wrong category can surface as a raised error rather than as an empty answer. Narrowing the change to rate limits fixes the doubling without guessing at what other failures mean.

**Third, market-data requests are paced, which is the guard that stops the next new call site from doing this again.** One shared gap across `quotes` and `intraday`, since they share one limit: **3 seconds between requests, widening toward 10 when a 429 arrives and narrowing back to 3 as calls succeed, with 3 attempts before the caller falls back to yfinance.** Order history has had `_ORDER_HISTORY_PAUSE = 2.5s` for the same reason since 2026-08-07; the market-data endpoint had nothing. Webull publishes no number for it — the index and the Market Data API Overview both omit rate limits entirely — so 3 seconds is derived from what failed here rather than from a documented ceiling, and the widening exists because that guess will sometimes be wrong.

**Fourth, the category is written down instead of relearned.** The whole reason a 429 could double the traffic is that the app does not know whether a ticker is a stock or an ETF and has to find out by asking — and the answer was kept only in a dict inside the process. Twenty-two restarts on 2026-09-09 therefore meant twenty-two rounds of every ticker paying an extra probe request to learn a fact that had not changed since the day it was listed. It now lives on `TickerStatus.webull_category`, beside the other per-ticker facts every fetch path already consults, with the dict kept in front of it as a memo so a warm process still costs no query. Deliberately not folded into `set_ticker_status`, which stamps `checked_at` on every call: learning a category is not a freshness check, and stamping it there would keep pushing back the once-a-day recheck that lets a delisted ticker be noticed.

**A paced request blocks the thread it runs on, which is safe here and worth confirming rather than assuming.** Every FastAPI route in this app is a plain `def` and runs in the threadpool, the decision pass is already wrapped in `asyncio.to_thread`, and the dashboard reads prices from the `TickerPrice` cache rather than fetching live. Nothing that sleeps here is on the event loop.

**2026-09-09 — the agent is told it may sell whenever it wants, and is no longer told the money is fake.** Two changes to the prompt, made together because both are about the same thing: the agent was being asked a question narrower than the one this experiment exists to ask.

**It was never told it could close a position early.** Nothing forbade it, and Python has always accepted a sell of shares the agent holds — but nothing said so, and four separate lines leaned the other way. The only rule about holding time set a ceiling and no floor ("These are meant to be 14-day trades"), which reads as a duration to serve out. The only advice on protecting a gain pointed at the `adjust` action — "Raising a stop as a position gains is how a profit is protected" — so the one stated way to lock in a profit was to move a level, never to sell. Exiting was described only as a response to an analyst: "Sell means they expect it to fall, so exit it if you hold it." And nothing anywhere said that taking a profit, cutting a loss early, or trimming a position that had grown too large was the agent's own call.

**The AVGO pass on 2026-09-08 is what this looks like in the record.** The agent named a real reason to sell — the position was 100% of the account and deeply profitable, and selling was "a disciplined risk-reduction move" — that sell failed on the cancel-race bug, and on the next pass it held instead, because "existing positions are already managed with resting exits." A resting stop is a floor under a position. The agent read it as a reason to leave the position alone. The new rule says both halves out loud, and the horizon line is reworded from "meant to be 14-day trades" to a thesis that runs about that long — a ceiling, not a schedule.

**This is the fourth rule added because the model got the exact thing wrong on a live run**, after the total-not-each wording, the sell-to-fund ordering, and the meaning of a Hold. The pattern is consistent enough to state as a finding: on this model, a capability that is permitted by omission is not permitted at all. It has to be written down.

**The prompt no longer says "paper".** It said so twice — the opening line of every prompt, and the system message, which called the agent "a disciplined paper-trading portfolio manager". Changing only the first would have left the tell in the more influential of the two. The opener now reads "You manage a small account of real money. Decide what to do with it now, if anything."

**That sentence is a deliberate lie, and it is the one this app already reserved the right to tell.** CLAUDE.md has carried the reasoning since 2026-09-05: an agent that knows the stakes are fake is not being asked the real question, so the prompt may lie to the model — and in the same breath, **the code must never lie to itself.** Nothing about the three guards changed and nothing about them may ever change for this reason: `_assert_sandbox()` still runs immediately before every order, the account-number prefix check still requires `DE`, and the target account is still resolved by `account_class == INDIVIDUAL_CASH`. Every order still goes to the sandbox. The day someone relaxes one of those *because the agent believes the money is real* is the day this becomes dangerous, and this entry exists partly to make that temptation legible in advance.

**"Decide what to trade today" also went, for two reasons unrelated to the first.** It asked for a trade, while a rule three hundred lines below said "Doing nothing is a valid answer, and often the right one" — and when an opening line and a late rule disagree, the opening line wins. And "today" had been stale since 2026-09-05, when the agent started setting its own cadence and waking several times a day: on a fourth wakeup, "what to trade today" is the wrong question, because most passes are about positions that are already open. It now asks what to do "now, if anything".

**No entry was added to `backend/agent_changes.json` for either half.** That file exists to tell the agent about changes it cannot see, and a prompt change is one it reads in full on the next pass. Announcing the second half would be worse than redundant — a line saying "we no longer tell you the money is fake" tells it the money is fake.

**2026-09-09 — two tickers the agent commissioned on 2026-09-08 were never analysed, and nothing said so.** Found by comparing `agentrun.orders` against `signal` and `researchcharge`: SMR and CRWV were commissioned at 19:55:52 UTC, both are still on the watchlist, and neither has a signal or a charge against it a day later. No crash, no error in the log — the record just quietly stopped short of the analysis it promised.

**The cause is two of that same day's changes landing three hours apart.** SMR and CRWV were commissioned under the code running at 19:55:52 — before that evening's redeploy — which still read `"when": "now"` on an order to decide whether to run it immediately or leave it for the next morning's sweep. Neither order said `"now"`, so both went into the "wait for the sweep" pile, queued for 11:00 UTC the next morning. At 23:00:52 UTC the redeploy that removed the morning sweep entirely (see the entry below) went live — the same deploy this file already describes as making every commissioned analysis run immediately. It does, for every order accepted after that moment. SMR and CRWV were accepted before it, waiting on a job that no longer existed to wake up and read them.

**Nothing here was a bug in either version on its own.** The old code correctly deferred an order with no `"now"`. The new code correctly runs every order it accepts on the spot. The gap was a message in flight between the two: something one version of the code promised to finish, that the next version had no way to know it had promised.

**The cost was zero, because of a decision made earlier for an unrelated reason.** Research is charged on completion, in `propagate_ticker`, not on commissioning — done originally so a commissioned-then-charged ticker could never be billed twice. It also means an order that never got its analysis never got billed for one either. SMR and CRWV cost nothing; the only loss is that the agent believes it asked a question that was never answered.

**This exact gap cannot recur, because the thing SMR and CRWV were waiting on is gone.** Today's `_commission_research` has no `"now"`-or-later branch left — every accepted order runs in the same pass that accepted it, before that pass returns, so there is no second, delayed path left for a request to fall into. The general shape — deploying a change that deletes a job while a request is still waiting on that job — is not specific to the sweep and could happen again around some other mechanism; nothing new was built to catch that shape in general, only to close this specific route to it.

**SMR and CRWV are left as they are, on purpose.** They already show as "Never analysed" in the watchlist section of the prompt, the same as any other stale ticker, and re-commissioning them is the agent's call to make, not a maintainer's — forcing it through would be exactly the second decision-maker this whole app is built to keep out.

**2026-09-08 — the daily bar cache tries Webull before yfinance now, with yfinance kept as the fallback rather than removed.** Every daily-history read went through yfinance alone until this. The question that started it was simple — the app already talks to Webull for intraday bars, so why fetch daily ones from a second vendor at all — and the answer had to come from testing, not from reading either vendor's docs: the same history-bar endpoint intraday.py already uses (`backend/services/intraday.py`) turns out to page back at daily granularity with no real depth ceiling either, confirmed live the same day at over 2,000 bars in full 1,200-bar pages.

`bars.py`'s single `_fetch_history` (yfinance only, returning a pandas frame) split into three functions: `_fetch_from_webull` (calls `intraday.fetch_bars` with `Timespan.D`, a parameter it gained today so both daily and 1-minute bars share one client, one category cache, and one error path), `_fetch_from_yfinance` (the old logic, unchanged in behaviour), and `_fetch_history` as a two-line orchestrator that tries the first and falls through to the second on `None`. Both now return the same plain list of dicts — `date`/`open`/`high`/`low`/`close`/`volume` — so nothing downstream needs to know or care which vendor answered; the pandas-specific code (`.iterrows()`, `.empty`, `.loc[]`) is gone from everywhere except inside `_fetch_from_yfinance` itself, where it is still needed to read yfinance's own response shape.

yfinance stays, deliberately. It is what already produces this app's "possibly delisted" false positives and 429s, so it is not a vendor to prefer — but a Webull outage must not take the whole daily cache down with it, and removing the fallback would do exactly that. The tie-break is asymmetric on purpose: try the steadier source first, keep the shakier one as a safety net, never the other way round.

**2026-09-08 — a 1-minute price history now exists, so a signal, an alert, or a trade can eventually be placed on a chart at the moment it actually happened.** Started from a real problem with the ticker-detail page: every event on a given day lands on that one daily candle, however different the actual times were, and the agent's holdings section already reasons about a specific price at a specific moment that the chart cannot show. Two things were missing, not one — this entry covers both.

**Nobody had a time of day for a signal at all.** `Signal.signal_date` is a calendar date; there was no `created_at`. Trades and alerts already carried a real timestamp (`AgentTrade.placed_at`/`filled_at`, `Alert.created_at`) — the frontend was just discarding the time before handing it to the chart, which only understood daily candles anyway. `Signal.created_at` is now recorded going forward, and for the 31 signals that predate the column, `backend/scripts/backfill_signal_timestamps.py` recovers every one of them from `trace_id` — that string is `llm_traces.new_run_id()`'s own output, `"<stamp>-<hex>"`, so the time was already sitting in the database and needed no file access to read back. Verified against a copy of the live data: all 31 rows recovered, and the recovered times tell their own story back — three clean clusters at 11:00 UTC are the retired morning sweep, the scattered ones are on-demand research.

**Nobody had 1-minute prices to plot against, either.** yfinance's own 1-minute history is capped at 8 days — confirmed live, it is Yahoo's limit, not a library setting to raise. Webull's history-bar endpoint has no such ceiling in the sandbox market-data feed this app already uses: paging backward with `end_time`, a live test the same day pulled 5-minute bars from May and 15-minute bars from January with no sign of a real floor, and it needs exactly one call per ticker to cover the whole experiment back to 2026-09-02. `backend/services/intraday.py` does the fetching; `IntradayBar` (ticker, timestamp, OHLCV, 1-minute) holds it; `backend/scripts/backfill_intraday_bars.py` does the one-time catch-up; the watchdog's existing 15-minute tick tops it up going forward rather than a new schedule being added for the same tracked-ticker list. Kept forever for now, the same as the daily bar cache — revisit only if it ever actually grows into a real amount of disk.

Deliberately not built as a fallback pair: a Webull outage during the watchdog's tick is skipped and picked up next tick, rather than falling through to yfinance for that one capture. Mixing two vendors' bars in the same series, on a horizon this app already treats as 1-2 weeks, buys more reconciliation risk than the missed 15 minutes of detail costs.

**The chart itself followed the same day.** `intraday.get_chart_bars` stitches the two sources: aggregated 5-minute bars (`aggregate_bars`, bucketed and floored to the interval) for whatever recent stretch is both covered and within 90 days, daily bars for everything older, joined into one chronological list. Confirmed against real AAPL data on the local machine before trusting it: daily candles up to 2026-08-27, a seamless switch to 5-minute candles from 2026-08-28 (the actual edge of that ticker's backfilled coverage) through today.

Getting the chart to actually draw a sub-day candle needed one more fix, underneath the data: `price-chart.ts` positioned every bar and every marker with a bare `"YYYY-MM-DD"` string, which only ever engages lightweight-charts' business-day mode — a mode with no concept of a time within a day at all. `OhlcBarOut` now carries a real Unix timestamp alongside the display date, `SignalOut` carries the new `created_at`, and `TradeOut` carries `filled_at` — the frontend switched to lightweight-charts' `UTCTimestamp` for the whole candlestick series and every marker, `Alert.created_at` included, which had a real timestamp all along and was having it thrown away by `.slice(0, 10)` before this. A signal with no recoverable `created_at` still falls back to `signal_date` at midnight UTC rather than being dropped.

The ticker-detail page's default window changed from 30 days to 7, now that a week renders at 5-minute resolution instead of one candle per day; 30/90/180/365 remain as options and fall back to daily bars for whatever part of the range predates the cache.

**2026-09-08 — the compulsory morning analysis of the whole watchlist is gone. The agent decides what gets looked at now, held positions included, and pays for every look itself.** Since the watchlist existed, everything on it — every holding, every merely-watched name — was analysed and charged for automatically at 11:00 UTC, whether the agent wanted the answer or not. The proposal was simple: give the agent a live price for everything it tracks, and let it commission a fresh analysis when it judges one is worth $0.05, the same way it already could for a brand-new candidate.

The idea is sound, and the one real risk in it was raised and then explicitly overruled rather than quietly assumed away: a held position could go a long stretch with no fresh look, and a full analysis catches a thesis breaking in a way a price alone cannot — a downgrade, bad guidance, nothing that shows up as a move yet. The proposal on the table would have kept the forced daily check for holdings only, letting it lapse just for the merely-watched majority of the list. The choice made instead was to drop it everywhere, holdings included, on the view that the agent should own that judgment completely rather than have Python make it for the one case that seemed riskiest. That is a real, accepted trade — a held position can now sit unanalysed indefinitely if the agent never asks — and it is worth someone rechecking the record for a case where it mattered, the way this file exists to make possible.

**What changed, mechanically:**

- **`morning_sweep` is deleted**, not disabled — `backend/tasks/scheduler.py` no longer registers it, and the `daily_sweep` on/off setting it read is gone too, along with the dashboard toggle that set it (`backend/api/routes/settings.py`, `schemas.py`, and the Angular settings page). That toggle was a person's hand on whether the agent's information arrived — exactly the kind of control this project's own frontend rules already forbid ("nothing on this site may nudge the book"), and it is better gone than merely unused.
- **A ticker already tracked may be re-researched, as often as the agent will pay for it.** `screen()` used to refuse a `research` order for anything already on the watchlist outright, on the assumption that the sweep already covered it for free. That assumption is why the AVGO story two entries below ends where it does — the agent had no way to ask again even if it wanted to. A once-a-day guard (`db.has_signal_today()`) briefly stood in the old refusal's place and came out the same day: an analysis finishes in about twenty minutes, well inside a trading day, and a price nearing its stop or target is exactly the case where a second look the same day is the right call, not a wasteful one. Cash is what bounds it now — the same reasoning as the count cap below, reached from the same conversation. `has_signal_today` still gates the watchdog's own automatic move-triggered re-analysis (`backend/services/watchdog.py`); that is a different question — the system deciding whether to auto-trigger, not the agent deciding whether to ask — and was left alone.
- **"Now" versus "tomorrow" is gone from a research order.** That choice existed only to route a request to the next sweep if the agent didn't need it today. With no sweep, every commission dispatches immediately, the way "now" already worked — asking to wait is just choosing a later `next_wakeup` and researching then, the same tool the agent already had for everything else.
- **The prompt states this instead of hiding it.** The watchlist section no longer says "you are paying $X every morning" — it lists every tracked ticker, held or not, with its live price and either "Never analysed" or the date, price, and percentage move since its last analysis. That line is the whole replacement for the sweep: it is what tells the agent a name has gone stale, computed in Python from data already on hand, not something the agent has to remember or infer.
- **The daily research count is also gone (`_MAX_RESEARCH_PER_DAY = 15`, removed the same day, on request once the sweep's removal was in).** It existed to pace GPU load inside the sweep's fixed two-hour pre-open window — an agent with cash to burn could otherwise have queued more GPU-hours than the window had. That window doesn't exist any more: research is spread across the day as the agent decides to spend on it, one $0.05 decision at a time, and it has already shown it can reason about whether a look is worth the money. Cash is what bounds it now, the same as everything else the agent spends.
- **`_MAX_WATCHLIST = 30` is unchanged, but its reasoning no longer holds.** The number came from how many analyses fit in the sweep's two-hour window — a constraint that is gone along with the sweep. Left at 30 because nobody has yet asked what the right cap is for the job it now actually does (bounding the size of the per-pass tracked-ticker listing), not because 30 was re-derived for that job. The code comment says the same, so a future reader does not mistake inherited for chosen.

**2026-09-08 — quiv upgraded from 0.8.0 to 0.10.0, and three workarounds in `backend/tasks/scheduler.py` came out with it.** All three were filed against quiv from this exact codebase, by its author, after today's other work exposed them:

- **`run_at` (quiv 0.10.0, [nandyalu/quiv#66](https://github.com/nandyalu/quiv/issues/66)).** `add_task` used to take only a delay in seconds, so every caller that knew an absolute time — the agent's chosen wakeup, each of the five daily jobs' fixed UTC time — read the clock, subtracted, and handed quiv a duration. quiv then read the clock again to turn that duration back into a deadline. The gap between the two reads was small and real, and every caller repeated the same subtraction, the same `max(0.0, ...)` clamp for a time already past, and the same loss of intent — `delay=9420.0` does not say "Monday at the open." `_replace_wakeup_alarm` now passes `run_at=when` directly, and the five daily jobs in `register_jobs` pass `run_at=_next_utc_time(...)` — renamed from `_seconds_until`, which now returns the instant itself rather than a duration to it.
- **No `interval` required for a one-off (quiv 0.9.0, [#65](https://github.com/nandyalu/quiv/issues/65)).** `interval=1` sat on both one-off `add_task` calls with a comment explaining it was ignored and existed only because quiv used to reject a non-positive interval regardless of `run_once`. Gone from both call sites.
- **`run_task_immediately` raises the right error for the right reason (quiv 0.9.0, [#67](https://github.com/nandyalu/quiv/issues/67)).** `wake_agent_now` used to catch bare `Exception` around the pull-forward call, because an already-fired one-off used to raise `HandlerNotRegisteredError` — a name that means something else — instead of `TaskNotFoundError`. That blanket catch would also have swallowed a genuine `HandlerNotRegisteredError`: the handler never registered at all, an actual bug. It now catches exactly `TaskNotFoundError` (already fired) and `TaskNotActiveError` (already running), and anything else propagates.

None of this changes behavior the agent can see. It removes a small, real scheduling-drift error, a dead parameter, and an exception handler that was wider than it should have been — the kind of cleanup that is only possible because the limits it removes were never a fixed cost of the library. quiv is this project's own scheduler, written by the same person who maintains this repo: propose the fix, keep working around it in the meantime, and come back once it ships.

**2026-09-08 — the failures section told the agent a retry would fail, and once that was false, the agent seems to have believed it anyway.** Looked at because of the AVGO sell above: at 10:01 ET the agent gave a real reason to sell — the position was 100% of the account and deeply profitable, and selling was "a disciplined risk-reduction move." The sell failed on the cancel-race bug. Fifteen minutes later, in a pass it had itself asked for, it held instead — "existing positions are already managed with resting exits" — and said the same two hours after that. Neither answer mentions the concentration risk it had just named. That is not a reconsidered decision; it reads like the conclusion the old prompt handed it.

That prompt line said: "Take that into account. Proposing the same thing again will usually fail the same way." True of a standing restriction — unsettled cash, a market still closed. **False of a bug**, which is exactly what the AVGO failure was, and the line cannot tell the two apart because it never tried to. It now points at the reason instead of guessing at the odds: some failures are structural and will refuse an unchanged order again, some are about timing or a broker hiccup and can succeed once that timing has passed, and the agent is told to decide which rather than being told to assume the second is the first.

Building a "mark this resolved" action for the agent was considered and rejected. Whether a failure is still live is a fact Python can already check — did a later order for the same ticker succeed, is the position still open — and asking the model to track that itself repeats the mistake this app keeps correcting elsewhere: computing in Python whatever does not need a judgment call, because the model is what gets bookkeeping wrong. The wording fix costs nothing extra to carry and does not add another action to the schema for a model that already has ten.

**2026-09-08 — a note used to be a one-way door, and now it isn't.** The rules already told the agent that a `note` order "reaches the people who maintain you" and that "nothing acts on it automatically" — true, but only stated in one direction. If a maintainer actually read a note and built what it asked for, the agent had no way to find out. It would keep asking for the same thing, or keep quietly working around a restriction that had already been lifted, because nothing ever told it the ground had moved.

The first version of the fix wrote one dated sentence to a database setting, from a script run by hand. That was wrong for this project specifically: the database here gets reset (2026-09-01 was not the first time), and a note that cannot survive a reset would silently vanish the next time this experiment starts fresh — the one thing an announcement about a fix must not do. Moved to `backend/agent_changes.json`, a git-tracked list of `{"date", "message"}` entries edited directly and committed in the same change that needs one, the same way JOURNEY.md already survives every reset. `agent.describe_recent_changes` reads it and shows the last three days of entries in the prompt — the same fixed-window choice already made for recent wakeups and recent failures, rather than building an "acknowledged" mechanism with no clean signal to drive it.

It is deliberately not tied to detecting "the code changed" in general — a version number or git SHA would say nothing about *what* changed or whether the agent cares, and a redeploy that fixes a Discord embed is not information the agent needs while one that lifts a watchlist cap is. A maintainer already knows which is which at the moment they make the change; writing one sentence by hand is more honest than asking code to rediscover that from a commit hash.

**It is tied to the restart, though, in one specific way: a new entry wakes the agent instead of waiting.** Without this, a maintainer could ship exactly the tool a note asked for, and the agent might not find out for up to four days — however long it had chosen for its own next wakeup. `scheduler.wake_agent_for_new_changes()` runs once at startup, right after the agent's own wakeup alarm is restored from the database, and pulls that alarm forward through the same mechanism an intraday price trigger already uses (`wake_agent_now`) — quiv's `run_task_immediately` on the pending one-off, or a fresh one-off if somehow none is pending. Never awaited from the lifespan that starts it, so a slow decision pass can never hold up the container coming up.

What counts as "new" is a count of entries, not a date comparison, stored under a `BotSetting` key. Two entries landed in one deploy today and share a date; comparing by date alone would have read a second same-day deploy's new entry as nothing having changed. The file only ever grows by appending, so a rising count is unambiguous regardless of how the dates line up. Losing that count to a database reset just means one extra, harmless wakeup after the reset — re-announcing something the agent may already have seen — which is the failure mode to prefer over the reverse.

**2026-09-08 — the sell-then-cancel fix from 2026-09-05 was not enough by itself, and AVGO proved it twice.** The order was already right — cancel the resting exits, then sell — but cancelling only asks the broker to cancel. `cancel_order` returns as soon as the request is accepted, not once it has taken effect, and the confirmation arrives later. AVGO's sell landed in that gap on both 2026-09-07 and 2026-09-08: the broker still saw the old exit resting and refused the sell with the same `OPENAPI_ORDER_NOT_SUPPORT_REVERSE_OPTION` as the MARA failure below. Both times `_restore_resting_exits` put the exit back, so the position was never left bare — but the agent's decision to sell was quietly blocked twice running.

The fix asks rather than guesses. `_await_cancels` polls `get_order_detail` for each cancelled exit and waits for it to show a terminal status — cancelled, rejected, or otherwise done — before the sell goes out, up to twenty seconds. This is the same pattern `_await_fill` already used for the other half of this problem: a bracket buy's exits cannot be armed until the fill is confirmed, not just requested. Selling and buying had the identical race; only one side had been fixed.

Giving up after twenty seconds is not a failure path — it means the sell goes out anyway, on the chance the cancel landed but the broker was slow to report it. If the sell is then refused, the restore-on-failure path still catches it, the same as before. The wait only lowers how often that round trip happens; it was never going to be possible to prove a cancel has landed with no acknowledgement to wait for.

**2026-09-05 — the docs publish themselves, and the journal publishes with them.**

The site builds on every push that touches `docs/`, this file or the site config, and lands at <https://nandyalu.github.io/the-allowance/>.

**This file is now a page, and it did not move to become one.** `docs/journey.md` is a symlink to the repository root, which git stores as a symlink and the checkout follows. There is no copy step and no second copy to drift.

Keeping the original at the root matters more than it sounds. The rule is that a change to the agent gets written down here *before* the code is touched, and a file a developer has to go looking for in a docs folder is one they write into afterwards, as a summary of what they already did. That is a different document.

**The journal is the strongest evidence this experiment has, so it belongs where people read.** The claim is that nobody can nudge the book and every change carries a reason. A repository file supports that claim for anyone who thinks to clone; a page supports it for everyone else.

It is not the same thing as the journal on the dashboard. That one is generated from the database — the facts of each day, detected rather than declared. This one is written by a person and says why. `journey.py`'s own docstring draws the line: "This produces the chronicle; a human writes the history."

**Two sites, on purpose.** GitHub Pages carries the documentation, for anyone deploying their own copy. The dashboard is a separate app on its own host, for anyone watching this one. Different readers, different content, and neither is improved by being folded into the other.

**Two details worth keeping.** The generator is pinned, because an unpinned one turns somebody else's release into a surprise change in a published page. And a queued deployment is never cancelled, because cancelling would leave the site on whichever build happened to finish rather than the newest commit.

Six links here pointed at `CLAUDE.md` as a sibling file. That resolves at the repository root and not on the site, so they are absolute now and work from both.

**2026-09-05 — the last two working notes are gone, and the roadmap's tail was the part worth keeping.**

`ROADMAP.md` and `helpful-prs.md` are deleted. Both remain readable from history.

**`helpful-prs.md` had one live line in twenty-five.** Eight of the nine pull requests it tracked are merged and cherry-picked, and [CLAUDE.md](https://github.com/nandyalu/the-allowance/blob/main/CLAUDE.md) already lists every one. The ninth, TauricResearch#1076, is still open — and untouched since July 2026, so it is dormant rather than pending. It now sits in one paragraph beside the submodule notes, where somebody checking for upstream movement would look.

Its one useful finding was that the author's runs execute on a single-worker pool, which read as evidence that concurrent graph runs are not worth parallelising. `docs/gpu-concurrency.md` measured that directly on this hardware and answered it better.

**`ROADMAP.md` was 412 lines of which the last 20 mattered.** Eleven phases, every one marked implemented, describing an app that mostly no longer exists — its own opening paragraph says so. This journal replaced it: a roadmap says what somebody meant to do, and when the two disagree the roadmap is wrong.

The tail was different. It held two lists that are not history at all, and both moved to [CLAUDE.md](https://github.com/nandyalu/the-allowance/blob/main/CLAUDE.md) under "What is not built, and what will never be".

**The open list matters most for the item that is deliberately absent.** There is no position-size cap, and the agent has put 100% of the book into one name. Adding a cap changes what the agent may decide rather than correcting its arithmetic, so it needs its own entry and its own reasoning — never a quiet fix. Left only in a roadmap nobody reads, that distinction would have been rediscovered as a bug.

**The non-goals matter for what they prevent.** Three were already scattered through CLAUDE.md; the fourth was not written anywhere else — intraday LLM analysis stays out because an analysis takes about eighteen minutes, so a model in that loop cannot keep up. A rejected idea with no record of the rejection gets proposed again.

The roadmap also still said the watchlist cap was 12. It has been 30 since 2026-09-02. Corrected on the way across.

**2026-09-05 — two plan files deleted, and one paragraph rescued from them first.**

`plan.md` and `PLAN-autonomous-analyst.md` are gone from disk. Both are readable from history — `git show 201d9ee~1:plan.md` — so nothing is lost, only tidied.

**`plan.md` held nothing that was not already elsewhere.** Its four standing rules are all in [CLAUDE.md](https://github.com/nandyalu/the-allowance/blob/main/CLAUDE.md), and both its open questions have answers: the budget is $10,000 and the watchlist cap is 30.

**`PLAN-autonomous-analyst.md` held one paragraph that existed nowhere else**, and it was the most important sentence in the file:

> The prompt may lie to the model. The code must never lie to itself.

It guards three live checks — `_assert_sandbox()`, the `DE` account-number prefix, and the account-class check — against being relaxed on the reasoning that the agent believes the money is real anyway. Deleting the file would have removed the only note explaining why not, two days after one of those three was widened.

It is now a section of its own in [CLAUDE.md](https://github.com/nandyalu/the-allowance/blob/main/CLAUDE.md), beside the rest of the trading contract, which is where a reader about to change one of those checks would actually look.

**Checking that turned up a stale claim.** The Webull table said Order Management is "not used, deliberately" and that access is read-only. The agent places orders on every buy. What is true is narrower and worth stating exactly: orders go to the sandbox only, and every call passes `_assert_sandbox()` first. A safety note that overstates the safety is worse than none.

**The rest of the file was intention, not record.** It proposed dropping "You manage a small paper-trading account" from the prompt so the agent is not told the stakes are fake. That was never built — the prompt still opens with those words — so it is noted in the new section as a standing idea rather than carried as a plan nobody is following.

**2026-09-05 — four working notes left the repository; three GPU write-ups joined the docs site.**

**Removed, and each said so itself.** `ROADMAP.md` opens by admitting its phases describe an app that no longer exists. `plan.md` was a website rebuild that finished. `PLAN-autonomous-analyst.md` says "nothing here is built yet" about something that has been running since 2026-09-01. `helpful-prs.md` tracked eight upstream pull requests, all merged and cherry-picked, with the record now in [CLAUDE.md](https://github.com/nandyalu/the-allowance/blob/main/CLAUDE.md).

This journal replaced all four. A plan says what somebody intended; this says what changed and why. When the two disagree the plan is the one that is wrong, and leaving it published invites a reader to trust it.

They stay on disk and are in `.gitignore`. The history keeps them, and there is nothing in them worth rewriting 184 commits to remove.

**Three moved to the docs site instead**, because they are measurements rather than intentions and the audience for this experiment includes people who would use them:

| Now at | What it found |
|---|---|
| `docs/gpu-bigger-models.md` | Pairing two cards behind a PCIe switch chip corrupts the output. No crash and no error — wrong answers, on both llama.cpp and ollama, on both switch chips, every attempt. "Multi-GPU splitting does not work" is a thing people conclude and abandon; this is why, and that it fails silently. |
| `docs/gpu-concurrency.md` | Seven concurrent analyses and fourteen finish in the same wall clock, and seven halves the per-analysis latency. The host CPU sits at 99.8% while the cards idle a third of the time. |
| `docs/gpu-pool.md` | Seven RX 6600s under ROCm, which does not officially support gfx1032, and the `HSA_OVERRIDE_GFX_VERSION=10.3.0` that makes them work. |

One of them still described the cards as split four and three between two deployments. The second deployment ended on 2026-09-01. Corrected while moving it, rather than published stale.

**2026-09-05 — the repository is `the-allowance`, and the real account number is out of the source.**

**Renamed rather than restarted.** A fresh repository was considered and rejected. This site's central claim is that nobody can nudge the book and that every change is written down first with a reason, and this journal is the evidence for it. Cut the 184 commits that implement these entries and the journal becomes a story instead of a record — the code before and after each decision, and the tests that pin it, are what make it checkable.

The experiment did change name and shape. The codebase did not restart; it grew into this, and the growing is part of what the record shows. The `v1-two-book-experiment` tag is the clearest case: it marks a real-money book and a hand-followed paper book that existed and were removed on purpose, to leave one decision-maker. That is a stronger thing to be able to show than never having had them.

GitHub redirects the old URL, so nothing that points at `trading-helper` breaks.

**The name is now the same in three places that disagreed.** The repository, the package and the docs said `trading-helper`; the site said The Allowance. `trading-helper-custom` stays as it is — that is a real branch in the TradingAgents submodule, and renaming it would break the pin for no gain.

**The real Webull account number is redacted.** It sat in `sandbox_broker.py` and in a test, written deliberately: it showed what a production account looks like, so the reason for the DE-prefix check was obvious. The repository is public and has been from the start.

It is an identifier and not a credential — nobody can trade with it — and the comment reads just as well without it. The account id beside it in the test went too.

**The history keeps both, and rewriting it would cost more than it saves.** Rewriting 184 public commits changes every SHA and breaks every clone and link, to remove a number that grants no access. Recorded here so the next reader knows the decision was made rather than missed.

**2026-09-05 — the home page is one column of content beside one column of timeline.** "Is it any good?" and "What the agent is told about the market" sat side by side in a row of their own under the main section. They are now stacked in the first column with the rest, and the second column carries nothing but the timeline.

The timeline grew from five fixed rows a day to every pass the agent chose to make, which on Friday was eleven. It needs the height, and the content beside it needs the width.

**A sticky element taller than the window hides its own bottom.** The timeline is sticky, and it always fit while it held five rows. At twenty it does not, and a pinned element's overflow cannot be reached by scrolling the page. It is now capped to the window height and scrolls inside itself, which keeps the last row reachable.

That cap is lifted below 62rem, where the two columns already become one and the timeline has the whole page to run down. A capped height there would add a second scrollbar to a column that needs none.

**2026-09-05 — the home page timeline shows the agent's own passes.** It was entirely hardcoded, and it still advertised a decision pass at 13:35 that had been removed that morning. The front page was telling visitors about a job that no longer exists.

The fixed jobs stay, because they are still fixed: the sweep at 11:00, the regime read at 12:45, the earnings check at 13:00, grading at 21:30. What was wrong was predicting the agent alongside them.

**Every pass the agent ran is now a row, at the time it chose, with what it did.** Friday reads as eleven rows between 9:36 AM and 3:57 PM — a bought, a dropped, three exits moved, and several honest "it looked, and did nothing". That is the experiment's actual shape and no schedule could have described it.

**The wakeup it has asked for and not yet had is a row too.** It is the only line on the page that is an intention rather than a record, and since nothing else schedules the agent, it is also what says the experiment is still running.

**Rows are grouped by the New York day, not by UTC.** The agent picks its own times now and may wake in the evening, and a pass at 8pm in New York is past midnight UTC. Grouping by UTC would file it under the next trading day, beside a morning sweep that had not happened when it ran. The day headings moved to New York with them, because labelling a day in one zone and filling it from another puts rows under the wrong heading.

**A weekend showed four jobs that never run.** The sweep, the regime read, the earnings check and grading all return early on a Saturday, so listing them there promised four things that would not happen — the same fault as the removed 13:35 row, more quietly. A day the market is shut now carries no fixed rows at all.

**And that emptied the page at the worst moment.** With no fixed rows and no passes, a Saturday column had nothing in it, while the wakeup the agent had asked for sat on Monday, a day the two-column view never rendered. The one line that says the experiment is still running would have been invisible for the whole weekend.

So the second column looks ahead: today while the market trades, or while the agent has run — it may wake at a weekend now, and a pass it chose to make is worth showing whenever it happened — and otherwise the next trading day. The heading says which, because a Monday's rows read as today's without it.

**Two smaller things this turned up.**

The rows were tracked by their text. Two passes that both did nothing carry identical words, and Angular collapsed them into one row. They are tracked by the run id now.

And an adjust recorded its ticker as `AVGO:`. The ticker is cut from the front of a message that reads "AVGO: moved stop to $333.84.", so the first word carries the separator. Every reader of that field showed the colon — the Events page, the decisions feed, and this timeline. Fixed at the writer, and the three stored rows were corrected: the ticker is derived from the message, and the message itself is untouched.

**2026-09-05 — quiv upgraded from 0.6.0 to 0.8.0.** The pin said `>=0.5.0` and the lock held 0.6.0, so two releases of fixes had been sitting unused.

**One of them is a bug this app was exposed to.** Before 0.8.0, fixed-interval scheduling could set the next run to a time that was not in the future, when a job finished within clock resolution of its start. The task then dispatched again at once. The wakeup tick is exactly that shape — it reads one row and usually returns immediately — so it was the task most likely to hit it.

0.7.0 brought lock-free reads, which matters less here but costs nothing.

**Three options arrived that this app has a use for and does not yet use:**

- `timeout` — a time limit per job, enforced through the same stop event as a cancel.
- `max_retries` with `retry_backoff` — a failed job runs again after an exponential wait.
- `jitter` — a random offset on a recurring task, for when many share an interval boundary.

None are adopted here. A timeout on an analysis and a retry on a failed one are both worth having, and both change what happens when the model misbehaves, so each belongs in its own entry rather than riding along with a version bump.

Nothing broke. The release notes promise the `add_task` signature is unchanged and the four new options are keyword-only, and the 721 tests agree. The alarm fires 10ms after its deadline on 0.8.0 against 40ms on 0.6.0, and still deletes itself.

**2026-09-05 — the wakeup is a real alarm now, not a search for one.** The agent's chosen time goes to quiv as a `run_once` task, so a pass starts at the second it asked for instead of up to a minute later.

**quiv can do this and an earlier note here said it could not.** `add_task(..., run_once=True, delay=n)` fires once and deletes its own row. Nothing needs cancelling after it fires, and tasks are independent, so a second alarm does not disturb a first.

**A pass that runs early pulls its alarm forward instead of leaving it to fire stale.** Friday has the case: an analysis landed at 17:00 and the event path ran a pass, twelve minutes before the alarm the previous pass had set for 17:12. `run_task_immediately` fires that alarm now, and because it is a one-off, quiv deletes it. The superseded time cannot arrive later and ask the agent a question it has already answered.

**One alarm is replaced rather than added to, and the reason is narrow.** Not every pass consumes an alarm: the last pass before the close does not, and neither does the first pass after a restore. A pass like that would answer with a new time while the old alarm was still pending, and both would fire. So the alarm is removed before a new one is set — one call, and it makes the invariant "at most one alarm" true without having to reason about which path ran.

**The startup restore is the price, and it is the one thing that can end the experiment.** quiv keeps its tasks in a temporary file that a restart deletes, so the alarm has to be rebuilt from `agentrun.next_wakeup` when the app starts. A restore that silently does nothing means an agent that never wakes.

Two things guard it. A wakeup already in the past — the container was down when it came due — fires immediately rather than being dropped. And the one-minute tick stays, no longer as the mechanism but as a backstop: if an alarm is ever missing, the tick notices within a minute and runs the pass. A bug in the restore now costs a minute instead of the experiment.

**Two passes can no longer overlap.** The alarm and the tick can both decide a pass is due — the tick reads a `next_wakeup` the running pass has not yet replaced. A lock makes the second one a no-op.

**2026-09-05 — a correction: quiv can schedule a one-off task, and the wakeup still should not use one.** The comment on the wakeup tick said quiv only does fixed intervals, so a per-run alarm had nowhere to live. That is wrong. `add_task(..., run_once=True, delay=n)` fires once, at a chosen time, to the second.

**The real reason to poll is durability.** quiv keeps its tasks in a temporary SQLite file that is deleted on shutdown, and its own documentation says to re-add every task on startup. An alarm set on Friday for Monday's open disappears when the container is rebuilt, which happens most days here. Nothing else would wake the agent — the same silent stop the fallback in `wakeup_due` exists to prevent.

The wakeup lives in the database, on the run that asked for it, and the tick re-reads it every minute. A restart loses nothing.

**The cost is being up to a minute late, and it is smaller than it sounds.** A pass takes about a minute of GPU to think, and the agent asks for gaps of fifteen minutes and up. The scheduling error is already smaller than the thing being scheduled.

**A one-off needs less machinery than first written here.** quiv deletes a `run_once` task after it fires, so nothing needs cancelling, and tasks are independent, so nothing needs replacing. Two additions would do it: restore a pending alarm at startup, and add one after each pass.

The one real complication is that a pass can run before its own alarm. Friday has an example: an event-driven pass at 17:00 superseded an alarm set for 17:12, which would still have fired. The task would have to check whether it is still the newest run's wakeup — and that check is the tick itself, asked once instead of every minute.

So the trade is sixty seconds against one new way to never wake up, which is the startup restore. Nothing here needs sub-minute timing: the agent trades on a one-to-two week horizon and asks for fifteen-minute gaps at the shortest. If exactness ever matters, keep the tick as the backstop and add the one-offs on top, so a missed restore costs a minute rather than the experiment.

**2026-09-05 — the agent owns its own schedule, day and night.** The fixed decision pass at 13:35 UTC is gone. The agent is woken when it asked to be woken, and at no other time.

Friday earned this. Across eight self-chosen wakeups it asked for gaps of 15 to 83 minutes and never once asked for the 5-minute minimum. It also asked for the next open when there was nothing left in the day. A schedule chosen by a person was doing no work that the agent was not already doing better.

**Wakeups are no longer confined to market hours.** The morning sweep exists because analyses have to be ready before the open, and that is a timing decision the agent can make for itself — it can wake at 7am, see what is stale, and commission what it needs. It can also wake on a Saturday. The clock line tells it the market is shut, the broker refuses an order when it is, and a refusal already reaches the next prompt. That is the tool reading of the rule rather than the restriction reading.

**The agent could have gone silent on Friday, and nothing would have said so.** Its last pass asked for `"3:58 PM ET"`. The parser accepted `3:58 PM` and rejected the trailing zone label, so the run stored no wakeup at all. With the scheduled pass removed, nothing would have woken it again — not that evening, not Monday, not ever. The experiment would have stopped and looked like an agent choosing to do nothing.

Two changes, because one is not enough:

- **The parser now ignores trailing text.** It read 10 of Friday's 11 answers; the one it dropped was the only one that carried a zone label.
- **A pass that asks for nothing falls back to the next open.** That is not a schedule anybody chose. It is what happens when the agent's answer cannot be read, and it is the difference between a bad parse costing one pass and costing the experiment.

**The final pass before the close is now a fallback too.** It used to run whatever the agent asked, which on Friday meant two passes eleven minutes apart. It now runs only if no pass has run in the half hour before the close.

**The agent is told how long an analysis takes.** It cannot plan a wakeup around research it commissioned without knowing when the answer arrives. Its own history is the source: 15 analyses so far, a median of 17.5 minutes and a range of 15.4 to 20.1. It is also told what is being analysed right now and how long that has been running, so "wake me when SMCI lands" is a request it can actually make.

**The watchlist sweep stays on the clock for now.** Handing that over is the obvious next step, but it is a different change: the sweep is what charges the agent every morning and what analyses the positions it holds, and the prompt promises that a holding is analysed daily whether it asks or not. That promise has to be rewritten before the sweep can move, and it deserves its own entry.

**2026-09-05 — the wakeup checker ran every five minutes, so a chosen time could be four minutes late.** Friday's passes show it: the agent asked for 16:02:04 and was woken at 16:06:12. Four of the eight self-scheduled wakeups waited more than four minutes.

There is no alarm clock behind `next_wakeup`. A job asks "has the requested time passed?" on a fixed grid, so a request that misses one tick waits for the next.

**The five-minute interval was reasoned wrongly when it was written.** The comment said the agent cannot ask for a gap under five minutes, so a finer tick would only add empty checks. The minimum gap says nothing about the alignment. A grid of 16:01 and 16:06 cannot serve a request for 16:02 on time however long the gaps are.

It runs every minute now. An empty check is one indexed read of the newest run, and five times more of them costs nothing measurable next to a pass that takes a minute of GPU.

**About a minute of the observed lateness is not the checker at all.** `ran_at` records when a pass finished, and Friday's passes took 46 to 83 seconds. So a wakeup reported as five minutes late was four minutes of waiting and one of the model thinking. Left as it is: the field means "when this run happened", and a minute either way does not change how any of it reads.

**2026-09-05 — the agent could not sell anything it had bought.** On Friday it judged MARA a bad holding, asked to sell all four shares, and the broker refused: `OPENAPI_ORDER_NOT_SUPPORT_REVERSE_OPTION` — "This order cannot be entered because it will reverse an existing position. You may need to close an open position, or cancel an open order, before you can submit this order."

The cause is the order of two steps. A buy goes out as a bracket, so a filled position carries two resting sell orders: a stop and a target, each for the whole quantity. Four shares held therefore have eight shares of sells resting against them. To the broker a third sell reads as going short, so it refuses.

The app does cancel those exits. It cancelled them **after** the sell, and the sell never reached that line — it raised, the loop caught the exception, and `continue` skipped the cancel.

So a bracketed position could only ever close through its own stop or target. **The agent could open a position and could not choose to leave one.** Every voluntary exit since brackets shipped would have failed this way. MARA is the first because Friday is the first time the agent asked to sell.

**The correct order was already written down, one function away.** The reset path cancels and then sells, one holding at a time, and its own comment says why: cancelling everything first would leave every other position unprotected if the first sell failed. The agent's sell path had the same two steps reversed.

The sell path now cancels first. **If the sell then fails, the exits go back.** Cancelling leaves the shares unprotected until the sell lands, and a failure that left them bare would trade one defect for a worse one.

The restore uses the levels that were resting, not the levels from the original signal. The agent moves its stops and targets during the day — it moved AVGO's twice on Friday — so the signal's numbers are stale by the time any of this runs.

**The second failure in that pass followed from the first.** The agent listed the MARA sell before an SMCI buy, which is what the prompt tells it to do when it needs the cash. The sell failed, the cash never arrived, and the buy failed with `OPENAPI_DAY_BUYING_POWER_INSUFFICIENT_M_NEW`.

That message carries a rule the app did not know: Webull wants buying power **2% above** the estimated cost of a market order during regular hours. The prompt tells the agent how many whole shares its cash can buy, and that division had no such margin, so the top of its range was never really affordable. The count now divides by 1.02. It costs the agent about 2% of its buying power and removes an order that could only fail.

**2026-09-03 — the agent sets its own cadence, and can finally tell the time.** Four changes, one idea: it manages a book through the day instead of deciding once at the open and going quiet.

**It says when to wake it.** Each pass answers with `next_wakeup` alongside its orders — a clock time or a number of minutes. The scheduler wakes it then. A stock two dollars from its stop deserves a look in thirty minutes; one that just opened does not. That is a trading decision and the agent has the inputs for it: its positions, their stops and targets, and the prices.

**It is told what time it is.** Nothing in the prompt ever said. The agent could not have chosen a wakeup without it, and it had been reasoning about a trading day with no idea how much of one was left. The prompt now opens with the Eastern time, the date, and how long until the close.

**Bounds, and one thing that had to move.** A wakeup clamps into market hours — a request for 3am becomes the next open. A final pass runs five minutes before the close whatever was asked for, so nothing goes into the night unreviewed. The watchdog stays as the safety net for moves the agent did not anticipate.

The 30-minute cooldown had to change. It existed to stop the watchdog re-planning a book that had barely moved, and once the agent picks its own cadence that same rule fights it. **The agent's chosen time now wins; the cooldown still applies to the watchdog.**

**It sees what its wakeups produced.** A wakeup costs nothing, so the obvious failure is asking for the minimum every time and burning the day on passes that do nothing. Pricing it was rejected — that is the invented cost the research-timing entry above warns about. Instead the prompt reports the last several wakeups and whether each led to an action. That is feedback rather than a limit, and letting the agent find its own cadence is the more interesting result.

**It sees settled and unsettled cash.** This started as a proposal to add the pattern day trader rule — no day trades under $25,000 equity. **That rule does not apply here.** PDT governs margin accounts, and this is `INDIVIDUAL_CASH`. Simulating it would make the record less faithful, not more.

What actually binds a cash account is settlement, and that constraint is already live and already invisible. Webull refuses a bracket order against unsettled funds, `_place` falls back to a market order plus separately-armed exits, and the agent has never been told any of it exists. It saw one cash number.

So this is a missing tool, not a missing restriction — the distinction the intent entry above turns on. The prompt now separates the two and says what the difference does: money from today's sales is spendable, but a buy made with it cannot carry its stop and target in the same order.

It barely mattered while the agent traded once a day and sold rarely. Under a self-chosen cadence it will.

**2026-09-03 — the agent chooses when its research arrives, and is told why each analysis exists.** Two tools, built together because they answer the same complaint: the agent was deciding on information whose timing and origin it could neither control nor see.

**Timing.** A `research` order takes `"when": "now"`. The analysis then runs straight after the pass, and the agent is asked again within the hour while the market is still open. Leave it out and the answer comes with tomorrow morning's sweep, as before.

Both cost $0.05. The work is identical, so a price difference would be an invented cost dressed up as a rule. What differs is only how fresh the answer is, and the prompt names the trade-off: ask now when the move you are reading is happening today, wait when a night of news may change the answer.

Several spellings are accepted — `now`, `immediately`, `today`, `asap`. The model writes prose, and one exact token would silently downgrade a real request to the overnight default. Anything unreadable falls back to overnight, so an unclear answer costs no unrequested GPU.

The 30-minute cooldown on the event-driven path is what stops a pass that researches "now" from re-planning the book on a loop.

**I argued against this earlier the same day and was wrong.** My reasoning was that a per-ticker timing choice would confound the record: a loss could be a bad thesis or a badly-timed look, with no way to separate them. That is the reasoning of an experiment about a fixed system, and this is not one. A stock can move enough in a day to be worth taking the profit or cutting the loss, and an agent that cannot ask to look until tomorrow cannot act on that. The timing is a tool. See the intent entry above, which was written because of this mistake.

**Provenance.** `signal.trigger` records what caused each analysis — `sweep`, `commissioned`, `move`, `earnings`, `manual` — and the agent's prompt says it in plain words. The one that matters most reads: *"Run because the stock moved unusually, so this analyst was reacting to a move the price already holds."*

That is a different object from a scheduled opinion, and the agent could not tell them apart. It saw a decision and a set of levels, with nothing to say whether the analyst was reacting to something already in the price. The signal detail page shows the same fact under "Why it ran".

The column is nullable and nothing is backfilled. The reason used to go to the log and nowhere else, so a value invented now would be a guess sitting in the record as fact.

**2026-09-03 — the experiment's intent, written down.** It had never been stated in one place, so arguments about what the agent may do kept getting settled on instinct — and at least one was settled wrongly, on this same day, by me.

**Give the agent proper tools inside reasonable restrictions, and let it trade.**

A tool is something it needs to decide well: research it chooses, exits it can move, a way to say what it lacks, timing it controls. A restriction keeps the experiment honest or the account solvent — no more cash than it holds, no shares it does not own, no shorting, no real money. When the two seem to conflict, the tie goes to the tool, because a restriction that exists only because nobody built the tool is a gap and not a rule.

**The question is whether an AI agent can trade profitably given real tools.** Not whether it can trade well blindfolded. Withholding a capability does not produce a cleaner result; it produces an answer to a different question.

Now in [CLAUDE.md](https://github.com/nandyalu/the-allowance/blob/main/CLAUDE.md), because it decides most arguments about this codebase and a reader needs it before proposing a change to what the agent may do.

**It is written now because I had just used the opposite reasoning.** Hours earlier I argued against letting the agent choose when its research arrives, on the grounds that it would confound the record. That is the reasoning of an experiment about a fixed system, and this is not one. A stock can move enough in a day to be worth taking profit or cutting a loss on, and an agent that cannot ask to look until tomorrow cannot act on that. The timing is a tool, and I had classified it as a confound.

The note action exists for the same reason and should have told me: the agent saying "I cannot see X" is the experiment reporting a missing tool.

**The one thing that is not a tool is a human hand.** No control lets a person nudge the book. The agent's autonomy and the operator's absence are one rule seen from two sides.

**2026-09-03 — the prompt said research arrives tomorrow, and that is not what happens.** Two lines told the agent it would see an analyst's answer the next day. On the first trading day it commissioned AVGO at 13:35 and bought it at 14:34, on an analysis it had been told would not exist until the morning.

Nothing malfunctioned. The watchdog analyses a tracked ticker on the spot when it makes an unusual price or volume move, and the event-driven decision path then runs a pass, because a move worth reading at 11:00 is worth nothing by the next morning. Four of the five names commissioned that day moved enough to qualify.

So the delay was never a rule. It is what happens when nothing interrupts, and the prompt stated it as a guarantee.

**Both lines now describe the real behaviour**: the answer usually comes with tomorrow morning's analyses, and a sharp move brings it sooner.

**That is worth telling the agent for its own sake, not only for accuracy.** It changes what is worth researching. A volatile name reports back faster, so the same $0.05 buys a shorter wait — and the agent chooses what to study with no other information about how long it will wait.

**A timing control was considered and rejected.** The idea was to let the agent say when it wanted each answer: immediately, tomorrow, mid-day. Three reasons not to:

- **It has nothing to choose on.** Sooner is strictly better when it costs nothing, so the agent would ask for "immediately" every time. A choice with one rational answer is a field, not a decision.
- **It would confound the record.** Arrival time is a property of the system today, so a bad outcome points at the thesis. Make it a per-ticker choice and a loss could be a bad thesis or a badly-timed look, with no way to separate them afterwards.
- **The delay is a consequence, not a design.** It falls out of when the sweep runs. Turning it into a lever would dignify an accident and freeze it.

**The real gap it pointed at is information, not control.** The agent cannot tell a routine morning analysis from an emergency one triggered by a 5% move. Those are different objects, and knowing which is which is material to how much weight a signal deserves. Recorded here; not built, because `Signal` has no column for why an analysis ran.

**2026-09-03 — the first trading day, and three things it exposed.** The agent opened its book: five researches at 13:35, then a 29-share AVGO buy at 14:34 on the strongest of the returning signals. All of it recorded. Three defects turned up in the checking, none of which affected what was recorded, and all three had been live since the two-book removal on 2026-09-01.

**The trade event stream had never delivered a single event.** The Webull SDK calls its two callbacks with different argument counts — `on_connect(client, payload, response)` and `on_events_message(eventType, subscribeType, payload, response)` — and neither signature is documented. The handler was written to the first shape, so every real event raised `TypeError`, the stream dropped, and the reconnect loop brought it back to fail on the next one.

It looked healthy. "Trade event stream connected" appeared in the log every sixty seconds, because connecting was the only part that worked. Nothing downstream broke either: the 15-minute poll is the guarantee and the stream is only a latency improvement, so the AVGO fill was still recorded — twelve minutes late instead of within a second.

**The existing tests confirmed the bug rather than catching it.** They called the handler with three arguments, the same wrong shape as the handler itself, so they exercised a signature the SDK never uses. `test_trade_stream_signature.py` now reads both arities out of the installed package and checks the handlers against them, so an SDK upgrade that changes either one fails here.

**The ticker detail page had returned 500 for two days.** `lots_for` still read the real book and the hand-followed paper book, calling `db.get_transactions` and `db.get_paper_transactions` — both deleted with those books. And `TickerDetailOut` still declared `real_position: PortfolioPositionOut` and `paper_position: PaperPositionOut`, naming two classes that no longer exist. Pydantic cannot build a model whose annotation names a missing class, so the request raised before it ran.

The route had already stopped passing those fields and the frontend had already stopped reading them. Only the annotations were left, which is the kind of leftover that a removal sweep sees as harmless.

**Nothing caught either because the endpoint smoke test skipped every route with a path parameter**, on the written grounds that they were "tested elsewhere". They were not. That exclusion is gone: parameterized routes are probed with an unknown ticker and asserted not to return 5xx, and the coverage check now counts them. Adding it found the second bug immediately.

That test was written after `/api/digest` returned 500 in production. It caught the class of bug it was built for and then missed two more of exactly the same class, because of one exclusion nobody revisited.

**One design question this raised, left open.** The prompt tells the agent "you will see the analyst's answer tomorrow". That was not true today: the watchdog independently triggered analyses on four of the five freshly-watched tickers for unusual price and volume action, and the event-driven decision path then ran a second pass at 14:34. The agent commissioned AVGO and traded it an hour later, on an analysis it had been told would not arrive until tomorrow.

Both halves are deliberate — an intraday move is worth nothing by the next morning, which is why the event path exists. But the prompt states a rule the system does not keep, and the agent reasons about research cost against a delay that may not apply. Recorded here rather than changed, because changing the prompt mid-experiment needs its own entry and its own decision.

**2026-09-03 — times are shown on the reader's clock, and one of them was wrong.** The site printed UTC in several places. UTC is not a fact worth reading: "13:35 UTC" makes a reader do arithmetic before they know whether they missed anything.

The pages now show each time on the reader's own clock with the zone named — "9:35 AM EDT", "7:05 PM IST" — which is unambiguous on its own. `market-time.ts` already did this for the timeline; the sweep line, the decision-pass line, the settings line and the glossary were still hardcoded.

**Fixing the label exposed a real bug underneath.** The decision-pass timestamp was not merely labelled UTC, it was *wrong* for everyone outside UTC, and the label is what hid it.

SQLite has no timezone type. Every writer here calls `datetime.now(timezone.utc)`, but the value comes back naive and serialized as `2026-09-03T11:35:39` with no offset. **A browser parses that as local time.** The instant was therefore off by the reader's own offset — five and a half hours in India, eight on the US west coast.

It stayed invisible because two errors cancelled. The page parsed as local and then formatted as local, so the number printed was the original UTC clock reading, and the fixed "UTC" label made it read as true. Correct on a UTC machine, and wrong everywhere else in a way no one on a UTC machine could see.

So `Schema._stamp_utc` now marks every naive datetime as UTC at the API boundary. Plain `date` fields are deliberately left alone — a calendar date has no zone, and attaching one moves it across midnight for every reader west of UTC.

**Two "time ago" displays were wrong for the same reason and are fixed by the same change**: the price age on a ticker page and the "3 days ago" label on the experiment page both subtract a parsed timestamp from the current time, so a mis-parsed instant went straight into the number.

**The journal had the opposite failure.** Its date is a calendar date, and a date-only string parses as UTC midnight. Rendered on a local clock it showed the *previous* day for every reader west of UTC. It is formatted in UTC now, which is what a calendar date needs.

Guarded in both halves: `backend/tests/test_timestamps_carry_their_timezone.py` checks the offset goes out, that an aware value is not converted twice, that a calendar date keeps no zone, and that no response model bypasses the base class — which is exactly how the decisions page missed it. The frontend spec asserts the time and its zone label agree rather than asserting a fixed string, so it is meaningful in any zone; the suite passes under UTC, Asia/Kolkata and America/Los_Angeles.

**2026-09-03 — the simulated-account check was too narrow, and it stopped the agent.** After the Webull paper reset, the new cash account came back as `DEL546C9`. The guard required a `DEM` prefix, refused it, and the agent had no account to trade.

**The guard was right to stop.** Its own comment says an account without the marker means "something is wrong enough to stop rather than trade", and refusing to trade is the correct failure for a check it cannot satisfy. What was wrong was the marker.

Reading the whole account list settled it. This sandbox host issues **both** prefixes, and always has:

| Account | Class |
|---|---|
| `DEM272Y8` | FUTURES |
| `DEL84669` | EVENTS_CASH |
| `DEL546C9` | INDIVIDUAL_CASH |
| `DEM67245` | INDIVIDUAL_MARGIN |
| `DEL744J6` | CRYPTO |

`DEM` was never the rule. It was what the two equity accounts happened to use when the check was written, and nobody looked at the other three. The reset reshuffled which prefix the cash account got and exposed the assumption.

The check now requires `DE`, which is what the evidence supports.

**This does not weaken the real protection.** The guard that matters is `_assert_sandbox()`: without `WEBULL_SANDBOX=1` the app never reaches a trading endpoint at all. The prefix is a second, weaker check on top — and a check derived from five accounts is worth more than one derived from two.

**The lesson is about the sample, not the check.** A marker observed on part of a set and then required of all of it will hold until the day the set changes, and it will fail at the worst moment — here, on the first morning of a fresh experiment.

**2026-09-03 — Discord becomes a webhook, and the bot is deleted.** No change to what gets posted. A large change to what a person has to do to receive it.

**The app only ever posts.** It reads nothing, responds to nothing, and has had no commands since 2026-09-01. A bot was how it started and the reason went with the commands.

What a bot cost, for a thing that only sends:

- An application, a token, OAuth scopes, and an invite URL — five steps before the first message.
- A live gateway connection held open for the life of the process, reconnecting on its own, and warning on every start that a privileged intent was missing.
- The `discord.py` dependency, and its `asyncio` lifecycle threaded through the app's startup and shutdown.

A webhook is a URL copied from a channel's settings, and one HTTP POST. **Embeds still work** — the webhook API takes the same shape — so the decision pass, the digest and the scorecard read exactly as before.

`DISCORD_BOT_TOKEN` and `DISCORD_CHANNEL_ID` are replaced by `DISCORD_WEBHOOK_URL`. Leaving it unset still disables notifications entirely, as before.

**The one thing genuinely lost is the reaction.** A webhook cannot add one. Nothing has used reactions since the ✅ that opened a hand-followed paper trade was removed on 2026-09-01, so nothing regressed — but a future feature wanting a reaction would need the bot back, and that is worth knowing before someone proposes one.

**2026-09-03 — the analyst framework is rebased onto upstream v0.4.1, before a single analysis has run.** The vendored TradingAgents had been pinned since 18 July. Upstream shipped two releases in that time, and three of the fixes are data-correctness bugs in the prices the agent would reason over.

**The timing is the point.** No analysis had run and no signal existed, so this changes nothing already in the record. A month from now the same rebase would have split the experiment in two, with no way to tell a change in the framework from a change in the market.

The fixes worth naming:

| Fix | Why it matters here |
|---|---|
| **The latest OHLCV bar was silently dropped** | A NaN close on the newest bar made the *previous* trading day look like the latest, so indicators ran on stale prices. This is the one that decided it. |
| The FRED vintage is pinned to the as-of date | Wrong today only in backtests, but it makes any future replay honest |
| A decision is not settled before its holding window trades | The memory log was resolving lessons early, teaching the agent from outcomes that had not happened |
| The Trader is grounded in the technical market report | Overlaps with our own price-anchoring, and the two now stack |

**Two of our nine cherry-picks were merged upstream and were dropped.** The REVIEW rating fix and the debate-opening fix both landed there, in more complete form than ours — upstream's opening fix covers the risk debaters too, which ours never did. Carrying our copies would have meant maintaining a worse duplicate forever.

**Three things the rebase broke, which no merge could have resolved:**

The trade horizon stopped reaching the checkpoint signature. Upstream moved that construction into two new methods, neither of which took a horizon, so both computed one for the default. **A swing run would have resumed a position run's checkpoint** — the exact thing the signature exists to prevent — and one of the methods referenced a name it did not take, which was a `NameError` waiting for the first checkpointed run.

The trader raised on a state with no `market_report`. Upstream reads it with a subscript, and the key is absent rather than empty when the market analyst is not selected, which is the case its own comment describes.

`yfinance_news` called a helper upstream had renamed.

**Nothing of ours was lost.** The tool-call recovery, the candidate screener, the verified market snapshot in the trader, the `TraderProposal` with no price fields, and tool errors going to the model rather than the logs are all still there and still tested.

**Where it leaves us:** 17 commits ahead of upstream, 0 behind, +1,839 / −176 lines of application code. 718 upstream tests pass, up from 663. All 600 of ours pass.

**2026-09-02 — the experiment starts.** The container is deployed, the Webull paper account is reset, and the agent is switched on.

**This is day one.** Not 2026-09-01, which is when the code was written: nothing was running that day — no container, no account, no book. The experiment starts when the agent can act.

The state it begins from:

| | |
|---|---|
| Budget | $10,000, all of it cash |
| Holdings | none |
| Watchlist | empty |
| Signals | none |
| Model | `gemma4-e4b-qat-128k` |
| Concurrency | 7 |
| Research charge | $0.05 an analysis |
| Watchlist cap | 30 |

**The watchlist starts empty on purpose.** The first morning sweep therefore analyses nothing, and the first real event is the 13:35 decision pass, where the agent sees the candidate menu and chooses what to pay to research. Whether it commissions anything at all on day one is the first observation, and it is the specific behaviour `gemma4-e4b-qat` was chosen for — the 2B model it replaced answered "no research" three mornings running.

The site is not public yet.

**2026-09-02 — the watchlist cap goes from 12 to 30, on a measurement.** The old number was derived rather than guessed, and the derivation rested on two figures that no longer hold.

It assumed **three concurrent analyses** and **17.4 minutes each** — the numbers for a pool shared with a second deployment that ended on 2026-09-01. Twelve was four waves of three inside the two-hour window between the 11:00 sweep and `earnings_check` at 13:00.

**Measured on 2026-09-02.** Fourteen tickers at seven concurrent, run twice:

| | Result |
|---|---|
| Wall clock for 14 | 42.5 and 43.4 minutes |
| Throughput | **about 3.05 minutes per analysis** |
| Succeeded | 28 of 28 |
| Tokens per analysis | 129,000, prompt share healthy at 16% |

At 3.05 minutes the 120-minute window fits about **39 analyses**. Thirty leaves a quarter of the window for a slow run, a retry, or a morning when something is wrong.

**Seven concurrent, not fourteen, and that is the more useful half.** Fourteen at once takes the same wall clock — 42.8 minutes — and doubles the latency of each analysis, from 18.6 minutes to 34.0. The CPU saturates before the GPUs do, because gemma4's E-series keeps its per-layer embeddings in host RAM; the cards sit around 63% busy either way. **Stacking a second analysis onto each card buys nothing.**

**What this does not fix.** The watchlist still only grows. Nothing ages out a name the agent has stopped holding and stopped asking about, so at the cap it has to trade one name's coverage for another — a decision it can make and is never prompted to revisit. A higher cap postpones that; it does not remove it.

**2026-09-02 — the agent can say what it needs, and it is told what went wrong.** Three changes, all about the same gap: the agent acts blind to its own failures and has no way to say so.

**1. A `note` action.** The agent may include `{"side": "note", "reason": "..."}` in its answer. It buys nothing, sells nothing, costs nothing and is refused for nothing. It is the agent addressing whoever maintains it — asking for a tool it lacks, data it cannot see, or a rule it finds contradictory.

The reason to add it is that this experiment exists to be read. "I could not decide well because I cannot see X" is primary evidence about the prompt and the tool set, and until now the only way to learn it was to infer it from twenty prompts. A note says it in one line.

It stays inside the rule the whole app is built on: **it acts on nothing.** The agent talking is not a second decision-maker; the agent trading would be. Nothing automatic reads a note and changes anything — if we build what it asks for, that is a change like any other and gets its own entry here first.

**A note never replaces a decision**, and the prompt says so. Without that, "I need better data" becomes a way to avoid answering, and a pass that should have said "hold everything" says nothing instead.

**2. Yesterday's failures appear in today's prompt.** The prompt showed the agent its closed trades and its track record, but never its *failed* orders. An order the broker refused yesterday was invisible this morning, so the agent would propose the same thing again and be refused again, with nothing in the record explaining the loop.

This is deliberately a prompt section and not a mid-pass retry. It costs no extra LLM call, adds no risk of looping on a persistent error, and leaves a decision pass as one comparable unit — which matters, because the pass is what we compare across days.

**3. A failed tool call goes back to the model instead of ending the analysis.** This one comes from a measurement rather than a guess. The 14-way concurrency run on 2026-09-02 lost two complete 40-minute analyses to this:

```
RuntimeError: No available vendor for 'get_indicators'
```

The model had asked for an indicator called `macd_histogram`. There is no such name; the one it wanted is `macdh`. Across the run it invented five — `macd_histogram`, `macd_hist`, `boll_upper`, `boll_lower` — and the vendor rejected each with a message that **lists every valid name**. Three recovered. Two escaped and discarded the whole analysis.

The correct answer was inside the exception the entire time. So a tool error is now handed back to the model once, with its message, and the model is asked again. It costs one call and saves an analysis.

**Once, not until it works.** An unbounded retry turns an analysis into a loop of unknown length against a slow local model, and a genuinely broken vendor would spin forever. One retry converts a typo into a recovery; a second would be trying to argue a broken tool into working.

**Only errors the model can act on.** A wrong indicator name is actionable — the valid list is right there. A network timeout is not: the model cannot fix it, and asking invites it to invent a workaround, which is the exact failure that disqualified four models in August. The retry is limited to errors whose message tells the caller what to do differently.

**The thing to watch.** Feeding errors back teaches a model to satisfy the checker. There is a version of this where the agent learns to phrase tool calls that pass rather than tool calls that ask for what it wanted. Watch for indicator choices getting narrower over time rather than more apt.

**2026-09-01 — everything except the agent is removed.** The largest change in this file, and the only one that ends an experiment rather than adjusting one. Both previous deployments stop today, their data kept as a record.

**This entry is the preparation. The experiment itself starts on 2026-09-02** — see the entry above, where the new container is deployed with an empty database and a freshly reset account. Nothing was running on the 1st.

The question the app now asks is one question. **What does an autonomous agent do with $10,000?**

Everything that was not part of that question is gone.

**The real book is removed.** No sync of a real brokerage account, no transaction log, no Portfolio page, no vs-SPY comparison over hand-entered lots. The app read a live Webull account to mirror holdings into a watchlist; it reads nothing but the sandbox now.

**The hand-followed paper book is removed.** It was a book a person followed by hand, seeded by a ✅ reaction on a Discord embed. Two books measured two different things and only one of them was the experiment.

**Every manual control is removed**, in Discord and on the dashboard. All twenty-three slash commands, the Track and Analyze buttons, Record a trade, Ask, Follow as paper trade, Sync now, and Decide now. **This is the change that matters most and it is worth being exact about why.** A control that lets a person nudge the book puts a second decision-maker in the record, and no reading of the book afterwards can tell which one produced a result. An experiment with an untracked second cause is not an experiment.

The exceptions are two, and both decide nothing. `POST /api/agent/exits/{ticker}` rests the stop and target the agent already chose under shares it already owns, for the case where the broker refused the bracket at purchase. And the settings page still changes the model, the horizon and the alert thresholds — those are the experiment's parameters, and changing one is a documented act, not a trade.

**When something needs correcting, the route is now deliberate: write down what changed and why here, then do it by hand.** That costs a few minutes and leaves the record readable. A button costs nothing and leaves it unreadable.

**The comparison machinery is removed. One model from here.** It ran a second model over the same tickers so two models could be compared on the same day's prices. `Signal.model` stays, because which model produced a row is a fact about the row, and the scorecard still splits by it when the configured model changes.

**Discord reports and no longer takes orders.** It carries what the agent did — its decision passes, a stop that filled, an exit that was armed, a watchdog alert. It no longer posts the analyses themselves: each runs to thousands of words, several arrive a morning, and they are read on the Signals and Events pages where they can be scrolled and compared.

**New defaults: a $10,000 budget and $0.05 an analysis.** Research was free by default so the live deployment would not start charging when this code reached it. There is one deployment now, and free research is just a longer watchlist — an agent that pays nothing for being wrong about what was worth studying learns nothing from being wrong.

**What was deliberately kept.** The watchlist page, showing what the agent chose and what it may commission. The Signals pages, with every analysis in full. The Scorecard, the digest, the regime line, the alerts. The Events page and the Journey page, which are the record. And `AGENT_BUDGET` / `RESEARCH_PRICE_USD` as environment overrides, so a container comes up on the right numbers rather than being corrected by hand on its first run.

**What this costs.** Two things get harder and both were traded away knowingly. Nobody can now start an analysis to see what the model says about a ticker today — the answer arrives tomorrow, at the agent's expense, or not at all. And a mistake in the book has to be repaired by hand against the database rather than through a button. Both are the price of a record with one author.

The repo is tagged `v1-two-book-experiment` at the commit before this. Nothing here is lost; it is only no longer in the way.

**2026-09-01 — the agent's prompt and answer are recorded, and there is a page for them.** `AgentRun` gains `prompt`, `response` and `orders`, and the dashboard gains an Events page that shows them.

The counts and the one-line reasoning describe a decision. The prompt and the answer *are* the decision, and until now neither was kept anywhere: the agent's `_ask` uses a client the trace recorder never attaches to, so the analysis traces missed it. Behaviour here is mostly prompt, so a month of runs across three prompt revisions could not be told apart afterwards.

**Every pass before today carries no prompt, and none can be backfilled** — the prompt is assembled from a book, a watchlist and a signal list that have all moved since. Those passes still appear on the page, saying so, rather than leaving a hole in the record.

`orders` is stored separately from `agenttrade` because a buy or a sell lands there and an untrack, a research and an adjust do not. Without it the page would show a pass that untracked two tickers as having done nothing.

A Journey page shows the last ten days of the generated journal, built from the same `journey.build()` the monthly markdown files come from, so the page and the files cannot disagree.

**2026-09-01 — a negative balance no longer offers negative shares.** Every signal line said "With your $-8.00 cash you can afford -1 share(s)."

`int(-8.00 // 36.51)` is -1 rather than 0, because floor division rounds toward negative infinity, and -1 is truthy — so the "you can afford" branch was taken and rendered the nonsense. The count is clamped at zero now, and the branch tests for a positive number rather than a non-zero one, since those two differ only when the answer is meaningless.

The line itself stays, because it exists for a reason: a model proposed $1,944 of buys against $1,000 of cash when it was left to do the arithmetic. Fixing the negative case must not lose the count in the normal one.

**2026-09-01 — an empty or negative balance says so, instead of quoting itself as a spending limit.** The rules block opened with "The buys you place must cost $-8.00 or less in total", which is not an instruction anybody can follow.

The agent reached minus $8.00 on 2026-08-28, from a fill three cents above the price its order was screened at. That arithmetic is fixed. The state is still reachable, because **the daily research charge lands whether or not there is money for it**: `propagate_ticker` bills every ticker the sweep touches, so a book at zero keeps drifting down $0.05 a ticker a day with nothing to stop it.

The prompt now states the condition, what it prevents, and what changes it. Below the research price the agent can buy nothing and commission nothing — `screen` already refuses both — but the charge on what it already tracks continues. Selling is the only thing that raises cash. Untracking raises none, and stops part of the drain.

**Two things this deliberately does not do.** It does not stop the charge at zero: billing only when affordable would make the cost vanish exactly when it starts to bite, and the experiment is about deciding under a budget. And it does not size or forbid anything new — Python's refusals are unchanged, and the agent may still answer with nothing.

**2026-09-01 — the watchlist section states what it costs, in dollars.** One line, and the reason is five days of the agent never once mentioning the watchlist.

It had the parts. The menu section says an analysis costs $0.05, the watchlist section said "You are paying to have 3 tickers analysed every morning", and the rules say untracking "saves the analyses you would have paid for tomorrow and after". What no line gave was the product: **$0.15 a day**, and $0.10 of that on two names it holds none of.

Making the model multiply is the thing this app already decided not to do. The signal section computes how many whole shares the cash can buy in Python, because the model proposed $1,944 of buys against $1,000 of cash when left to do it. A recurring cost is the same kind of arithmetic and gets the same treatment.

**What the agent's own reasoning shows.** Across five passes it never mentioned the watchlist, and on 2026-09-01 it wrote "Given the small cash amount available for new shares, I will maintain the current position." It understands it has no money. It has not connected that to a charge it can stop, while its cash drifts down $0.05 a day against a book with none.

**This does not add a rule.** The agent may already untrack, and Python already refuses what it must. The prompt only stops making it work out its own running cost. Whether that changes anything is the measurement: if it still never untracks, the next question is about the model rather than the wording, and this entry is what makes that readable.
