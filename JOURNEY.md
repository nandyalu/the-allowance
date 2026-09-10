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

## What belongs here, and what does not

**One question decides it: does this change make two periods of the experiment non-comparable?** If yes, it goes here. If no, it goes in [the changelog](https://github.com/nandyalu/the-allowance/blob/main/docs/changelog.md).

That splits into three tests. Any one of them is enough:

- **Behaviour** — it changes what the agent is shown, what it may ask for, or what Python refuses.
- **Evidence** — it changes what the record contains or means. Telemetry counts: a field that is null before a date is exactly what trips up whoever reads the data later.
- **Incident** — the agent's behaviour changed without anyone intending it, so real days are contaminated.

Everything else is a changelog entry: setup, deployment, guards, infrastructure, site copy, docs, dependencies. Those matter, and they are not this.

**Keep an entry to a sentence or two — what changed, and why.** Long-form reasoning that constrains a future edit belongs in `CLAUDE.md`, which is read before the code is changed. This file answers "when did the question change", and it can only do that if it stays readable end to end.

Entries before 2026-09-11 were swept under these rules; anything that failed all three tests moved to the changelog.

## Every change to the agent, and why

**This file covers one agent: the merged agent that has run since 2026-09-01.** Before that date, two deployments ran side by side — a live bot on a fixed watchlist, and a separate analyst experiment that chose its own tickers. Both ended on 2026-09-01. Their history lives in [the two-book experiment](https://github.com/nandyalu/the-allowance/blob/main/docs/two-book-experiment.md) and [the analyst experiment](https://github.com/nandyalu/the-allowance/blob/main/docs/analyst-experiment.md).

`CLAUDE.md` describes what the rules are. This describes how they got that way. Add an entry here **before** changing a rule, not after.

Newest first.

**2026-09-10 — the agent is asked when the market is shut, instead of being turned away at the door.** `run_once` refused every pass outside market hours, so the pre-open research the prompt invites it to do produced nothing at all — no research, no exit adjustment, not even a note. The refusal now falls on the order, which the broker rejects and reports into the next prompt.

**2026-09-09 — the model's reasoning is kept, after being generated, paid for and discarded since the day the agent started.** Roughly nine tenths of what the model produced was never recorded, so the record held every decision and none of the working-out. Passes before this date store nothing, and nothing is backfilled.

**2026-09-09 — a decision pass records what it cost: prompt tokens, completion tokens and seconds.** Nothing had ever counted them, so no question about what a prompt change costs could be answered. Stored NULL before this date and never zero, because a zero would read as a free call.

**2026-09-09 — the agent may sell whenever it judges it right, and is no longer told the money is fake.** A resting stop is a floor under a position, not a reason to leave it alone — and an agent told the stakes are imaginary is not being asked the question this experiment exists to ask.

**2026-09-09 — two tickers the agent commissioned on 2026-09-08 were never analysed, and nothing said so.** SMR and CRWV produced no signal, no charge and no error, so the agent spent the next day deciding around research it had ordered and never received.

**2026-09-08 — a signal records the time of day it was created, not only the calendar date.** Every event on a day had collapsed onto one daily candle. `Signal.created_at` is null for anything before this date.

**2026-09-08 — the compulsory morning analysis of the whole watchlist is gone.** Everything tracked was analysed and charged for at 11:00 UTC whether the agent wanted the answer or not; it now commissions every look itself, holdings included, bounded by cash rather than by a schedule.

**2026-09-08 — the failures section no longer tells the agent a retry will usually fail.** That stopped being true once the underlying bug was fixed, and the agent appears to have believed it anyway — holding a position it had just given a good reason to sell.

**2026-09-08 — the agent is told when a note it left has been acted on.** A note reached maintainers and nothing ever told the agent the ground had moved, so it kept asking for things that already existed. Entries in `backend/agent_changes.json` from the last three days now appear in the prompt.

**2026-09-08 — a sell waits for the exit cancellation to take effect, not merely to be accepted.** `cancel_order` returns before the broker has acted, and AVGO's sell landed in that gap on two consecutive days.

**2026-09-05 — the wakeup is a real alarm, fired at the second the agent asked for.** Polling for it meant a chosen time could arrive minutes late.

**2026-09-05 — the agent owns its own schedule, day and night.** The fixed 13:35 UTC pass is gone: it is woken when it asked to be woken, and at no other time.

**2026-09-05 — the wakeup checker ran every five minutes, so a chosen time could be four minutes late.** Four of eight self-scheduled wakeups waited more than four minutes, which makes the agent's own timing decisions unreadable afterwards.

**2026-09-05 — the agent could not sell anything it had bought.** Its own resting exits made every sell look like a position reversal to the broker, so the exits are now cancelled before the sell goes out.

**2026-09-03 — the agent sets its own cadence, and can finally tell the time.** It manages a book through the day instead of deciding once at the open and going quiet.

**2026-09-03 — the agent chooses when its research arrives, and is told why each analysis exists.** It had been deciding on information whose timing and origin it could neither control nor see.

**2026-09-03 — the experiment's intent is written down.** Give the agent proper tools inside reasonable restrictions and let it trade; where the two conflict the tie goes to the tool, because a restriction that exists only because nobody built the tool yet is a gap and not a rule.

**2026-09-03 — the prompt no longer claims research arrives tomorrow.** On the first trading day the agent commissioned AVGO at 13:35 and bought it an hour later, on an analysis it had been told would not exist until the morning.

**2026-09-03 — the first trading day, and three defects it exposed.** Five researches and a 29-share AVGO buy, all recorded correctly; the three faults had been live since the two-book removal and none of them touched the record.

**2026-09-03 — the simulated-account check was too narrow and stopped the agent.** It required a `DEM` prefix and the reset paper account came back as `DEL546C9`, so widening it to `DE` corrected a wrong observation rather than relaxing a guard.

**2026-09-02 — the experiment starts.** The container is deployed, the paper account is reset, and the agent is switched on with an empty book and nothing on its watchlist.

**2026-09-02 — the watchlist cap goes from 12 to 30, on a measurement.** The old number was derived rather than guessed, and both figures behind the derivation had stopped holding.

**2026-09-02 — the agent can say what it needs, and is told what went wrong.** It had been acting blind to its own refusals and broker failures, with no way to report a tool it was missing.

**2026-09-01 — everything except the agent is removed.** Both previous deployments stop and every manual control goes with them, because a person who can nudge the book puts a second decision-maker in the record and afterwards nothing can say which one produced a result.

**2026-09-01 — the agent's prompt and answer are recorded, and there is a page for them.** Behaviour here is mostly prompt, so a run whose prompt was not kept cannot be analysed afterwards.

**2026-09-01 — a negative balance no longer offers negative shares.** Every signal line had been reading "With your $-8.00 cash you can afford -1 share(s)."

**2026-09-01 — an empty or negative balance says so, instead of quoting itself as a spending limit.** "The buys you place must cost $-8.00 or less in total" is not an instruction anybody can follow.

**2026-09-01 — the watchlist section states what it costs, in dollars.** One line, after five days of the agent never once mentioning the watchlist.
