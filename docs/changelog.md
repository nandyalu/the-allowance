# Changelog

**Everything that changed about the app but not about the agent.** Deployment, setup, guards, infrastructure, the site, the docs and dependencies.

Changes to what the agent does, what it is shown, or what its record contains go in [the journey](journey.md) instead, and that page states the test. The split exists because the journey answers one question — when did the experiment's question change — and it can only answer it if the reader is not wading through image builds and CSS.

Entries are one or two lines: what changed, and why. Newest first.

## 2026-09-10

- **Setup** — The account check asks the broker whether the named account exists, instead of only checking the variable holds something. A second deployment reported ready with a number the sandbox no longer issues, while every pass logged "this deployment will not place orders" — the one page whose job is to make that visible was the page saying it was fine. The LLM check already drew this distinction; the account check had not.

- **Docs** — Three more skills in `.claude/skills/`, each built from something that actually went wrong: `review-contribution` for the rules a test cannot judge, `model-change` for the acid test that rejected five of six models, and `incident` for working out which days a silent fault contaminated. Every SQL query in the last one was run before it shipped.
- **Docs** — `CONTRIBUTING.md` and `AI_POLICY.md` added, both on the docs site and linked from the README, which also gains a licence section it never had. Contributing asks for a `Signed-off-by` line plus a grant to release the contribution under any licence, so PolyForm Noncommercial's commercial option survives contact with contributed code.
- **Tests** — Four invariants that were held by prose alone are now pinned by tests: every order path asserts the sandbox and the order API is reachable from one module only; the write surface is exactly the two routes that decide nothing; CLAUDE.md's quoted prompt matches the code, and the three rules that exist because of a live failure are still in it; and no module awaits a single-ticker analysis inside a loop. Each was verified by breaking the invariant and watching the test catch it.
- **Tests** — The frontend suite ran with eight unhandled errors, dismissed for weeks as a `lightweight-charts` quirk. jsdom does not implement `matchMedia`; `src/test-setup.ts` polyfills it and the count is zero. The real gain is that `chart-theme.ts` calls it unguarded, so the theme path had been throwing on every chart test and is now exercised.
- **Docs** — Every page audited against the code. Three instructions could not have worked: the setup page named a variable the app never reads (`LLM_BACKEND_URL`, against the real `TRADINGAGENTS_LLM_BACKEND_URL`), the README and two pages pointed at a compose file that `.gitignore` excludes, and the now-required `WEBULL_ACCOUNT_ID` appeared nowhere at all.
- **Setup** — `compose.example.yaml` is tracked, and `.env.example` rewritten. The old one still offered `DISCORD_BOT_TOKEN` for a bot deleted on 2026-09-01 and marked `WEBULL_SANDBOX` optional.
- **Docs** — A second pass fixed nine more: the README scheduled the day's final pass in UTC when the code reads it off the Eastern close, three removed slash commands were still documented, four renamed pages were still linked by their old names, and two figures were the previous model's.
- **Site** — Copy no longer states this deployment's history as fact. A decision card read "Passes before 2026-09-01 were not recorded" on a container built that morning, four strings promised a weekday schedule removed on 2026-09-05, and one told the reader to press a "Decide now" button deleted on 2026-09-01.
- **Site** — The research charge is served by `/api/settings` rather than written into six templates as "$0.05". Free research is a supported mode, so a deployment charging nothing had been telling every reader it charged five cents.

## 2026-09-09

- **Setup** — A first-run page at `/setup` reports what is missing and shows the lines to paste. It reports whether each requirement is satisfied and never what it is satisfied with, because the settings payload is published to the static site.
- **Deployment** — `WEBULL_ACCOUNT_ID` names the one simulated account a container may trade, with no default. The three existing guards resolve to the same account for every deployment applying the same rule, so a second container would have traded the first one's book.
- **Deployment** — The experiment's start date is stamped when the agent is first switched on, instead of being compiled into the frontend bundle. Every image built from this repo had claimed the first deployment's start date. It is also the floor for the 1-minute bar backfill, so a deployment starting months from now does not page back to somebody else's date.
- **Infrastructure** — LLM calls back off when a vendor returns 429, using the vendor's own `retry-after` header rather than a guessed ladder. One pace is shared across concurrent analyses, because the limit belongs to the account and not to the run.
- **Infrastructure** — The model list is authenticated and sends a real `User-Agent`. A metered endpoint returned 403 for both reasons at once, and the settings page silently degraded to a free-text field.
- **Data** — Webull had been rate-limiting most market-data calls all day and nothing said so, because every path falls back to yfinance. The watchdog's fifteen-minute tick was firing about twenty unpaced requests, and a 429 was being read as a failed category probe, which doubled the traffic causing it.

## 2026-09-08

- **Data** — The daily bar cache tries Webull before yfinance, with yfinance kept as the fallback rather than removed. The same endpoint used for intraday bars pages back at daily granularity with no real depth ceiling, and a Webull outage must not take the whole cache down.
- **Data** — A 1-minute price history is collected and backfilled, so a chart can show a signal, an alert or a trade at the minute it happened rather than on that day's single candle. Covers roughly the last 90 days; anything older is still daily bars.
- **Dependencies** — quiv 0.8.0 to 0.10.0, removing three workarounds in the scheduler that had been filed against quiv from this codebase.

## 2026-09-05

- **Docs** — The documentation site publishes itself, and the generated journal publishes with it.
- **Repository** — Renamed to `the-allowance`, and the real account number taken out of the source.
- **Repository** — Working notes and plan files removed; three GPU write-ups moved to the docs site, and the roadmap's tail kept.
- **Site** — The home page is one column of content beside one column of timeline, and that timeline shows the agent's own passes. It had been hardcoded, and still advertised a 13:35 decision pass removed that morning.
- **Dependencies** — quiv 0.6.0 to 0.8.0. The pin allowed it and the lock had not moved, so two releases of fixes sat unused.
- **Infrastructure** — A correction: quiv can schedule a one-off task, so the earlier note claiming otherwise was wrong. The wakeup still polls, because quiv's task store is deleted on shutdown and an alarm set on Friday for Monday would not survive a rebuild.

## 2026-09-03

- **Site** — Times are shown on the reader's clock. UTC made a reader do arithmetic before knowing whether they had missed anything.
- **Notifications** — Discord becomes a webhook and the bot is deleted. Nothing changes about what is posted; a great deal changes about what a person has to set up to receive it.
- **Analysis** — The vendored TradingAgents is rebased onto upstream v0.4.1, before a single analysis has run. Three of the fixes are data-correctness bugs in the prices the agent would reason over, and doing it later would have split the experiment with no way to tell a framework change from a market one.
