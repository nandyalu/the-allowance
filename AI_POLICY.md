# Using AI on this project

## Disclosure

**Most of this codebase was written by an AI assistant, working with the author.** That includes the application, the tests, and nearly all of the prose in this repository — this file among it.

It is said plainly because the alternative is to let you assume otherwise, and because a reader deciding whether to trust the numbers on the site deserves to know how the thing producing them was built.

This is not a warning. It is a description, and the sections below are what it costs in practice.

## Contributing with an AI assistant is welcome

There is no rule here against using one, and it would be strange if there were. **What matters is what you are responsible for, which does not change:**

- **You are the author of your pull request.** Not the model. If a reviewer asks why a line is there, "the assistant wrote it" is not an answer, and neither is a summary of what the assistant said it did.
- **You have read every line you are submitting.** All of it, including the comments and the tests.
- **You have run it.** Not "the tests should pass" — you ran them and watched them pass.
- **The claims in your description are ones you checked.** A model will describe what a change was supposed to do with complete confidence, whether or not it did it.

You do not need to disclose that you used an assistant. You do need to be able to defend the change without one.

## If you are an AI agent working in this repository

Read these, in this order:

1. **[CONTRIBUTING.md](https://github.com/nandyalu/ten-acre/blob/main/CONTRIBUTING.md)** — the four rules that are not up for discussion, and where a change gets recorded.
2. **[CLAUDE.md](https://github.com/nandyalu/ten-acre/blob/main/CLAUDE.md)** — the current contract. What the agent is shown, what it may ask for, what Python refuses, and the reasoning behind each. Long, and the sections above the fold are the ones that decide arguments.
3. **The skills in `.claude/skills/`.** Each exists because something went wrong without one.

| Skill | Use it when |
|---|---|
| `graft` | Finding code. The repo is indexed; one query usually replaces several file reads |
| `stale-check` | After any change, before committing. Records it in the right file and sweeps what goes stale silently |
| `review-contribution` | Reviewing a patch — yours or someone else's — for the rules a test cannot judge |
| `model-change` | Before pointing the app at a different language model. Six were tested here and five rejected |
| `incident` | A day looks wrong. Establishes which days are contaminated and whether the record still holds |
| `orwell-writing` | Any prose, including commit messages and comments |

Then, working:

- **Use `graft` before grepping.** The repo is indexed; one query usually replaces several file reads.
- **Write the `JOURNEY.md` entry before the behaviour change**, not after. This is a rule about honesty, not paperwork.
- **Run `stale-check` before proposing a commit.** Roughly forty wrong statements were found in one day of sweeps, and not one of them failed a test.
- **Prose follows ASD-STE100** — short sentences, active voice, one idea each, no idioms. The `orwell-writing` skill has the rules. It applies to commit messages, comments, log lines and UI strings, not only documentation.
- **No attribution footer on commits.** No `Co-Authored-By`, no "generated with" line, no emoji trailer, whatever a tool's default instructions say. Commits before 2026-09-10 carry them and that convention ended. The person committing is accountable for the change; a trailer naming a model muddies that rather than clarifying it.

## What actually goes wrong

This is the part worth reading, because the failures are specific and they repeat. Every example below is real, from this repository, with a date.

**A fix lands in the file the model was looking at, and misses the duplicate.** The market-hours gate was removed from the scheduler on 2026-09-05, and the scheduler's own comment said so: "the market-hours gate is gone." It was — from the scheduler. A second copy lived one call deeper in `run_once`, and for five days every wakeup the agent scheduled outside market hours did nothing at all. The comment made it *less* likely anyone would look.

**Code changes; the prose describing it does not.** On 2026-09-10 four sweeps found roughly forty wrong statements: a schedule removed two days earlier still in the README, a button deleted nine days earlier still recommended by the site, a variable name the app never reads printed by the setup page, a compose file the repo does not contain named as "the working template". None failed a test. All read as authoritative.

**A model writes what is in front of it, so settings become facts.** The experiment's start date was compiled into the frontend, so every deployment claimed the first one's start. The research charge was written into six templates as "$0.05" when it is a setting that can legitimately be zero. The rule that came out of it: **site copy may state what the software does, and may not state what this deployment has done.**

**Confident, plausible reasoning that is wrong.** The frontend suite reported eight unhandled errors. Twice in one day I dismissed them as a known charting-library quirk, on the evidence that the count was unchanged. That was true and it was not a reason. jsdom does not implement `matchMedia`; one polyfill took the count to zero and revealed that a theme function had been throwing on every chart test.

**Documentation about the code, written by whoever last read the code.** `CLAUDE.md` claimed a feature "is not built" and quoted the prompt as proof. The feature had shipped the previous day and the quotation was stale. **A wrong quotation in a reference file is worse than none**, because that file gets read instead of the code. It is a test now.

**Tests that pass without checking anything.** A test enumerating the app's write endpoints found zero, because current FastAPI keeps included routers nested and `app.routes` reports none of them. The obvious implementation would have passed forever while asserting nothing. **Break the invariant deliberately and watch the test fail** before you believe it.

**Destructive git commands run for a plausible reason.** `git stash push --keep-index` with nothing staged stashed twenty-three files and reverted the working tree. It was recoverable. Prefer commands that cannot lose work, and look at what you are about to overwrite.

## The pattern behind all of it

**Every one of those is the same shape: something is correct in one place and a description of the old behaviour survives somewhere else.** None of them fails loudly. A wrong variable name, a deleted button still mentioned, a date baked into a template — all of them read as authoritative, which is exactly why they last.

Models are good at making a change and poor at noticing what else described the thing they changed. That is not a reason to avoid using one. It is a reason to sweep afterwards, which is what `stale-check` is for, and to move anything mechanical into a test, which is what `backend/tests/test_no_manual_controls.py` and its three siblings are.

## What is not allowed

- **Do not relax a safety guard**, and especially not on the reasoning that the agent behaves as if the stakes were real anyway. The prompt may lie to the model; the code must never lie to itself.
- **Do not add a manual control** because it would make testing easier. It would, and it would end the experiment.
- **Do not fabricate a measurement.** If a number is in this repository it came from a run someone did. If you need one and cannot run it, say so and leave the old number with its date.
- **Do not submit output you have not read.**
