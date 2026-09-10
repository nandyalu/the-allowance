/**
 * When this deployment's experiment began.
 *
 * **Served by the API, not compiled in.** `/api/settings` carries
 * `experiment_start`, and `SettingsService` writes it here on load. The date
 * below is only what to say before that arrives, and when a deployment sets
 * nothing.
 *
 * It stopped being a constant on 2026-09-09, when a second container came up
 * and its home page said "day 8" — the date was baked into the bundle, so
 * every image built from this repo claimed the first deployment's start
 * however long that particular container had been running.
 *
 * Still one place a reader looks, which is what the old note here was about:
 * a start date written in four places drifts. It just resolves through a
 * setting first now.
 */

/**
 * **2 September 2026** — the first deployment's start, and the answer whenever
 * a deployment sets nothing.
 *
 * Not 1 September. The code that removed every manual control was written that
 * day, and the journal records it under that date because that is when it
 * happened. But nothing was running: no container, no account, no book. The
 * experiment starts when the agent can act, and that was the 2nd.
 */
export const DEFAULT_EXPERIMENT_START = new Date(Date.UTC(2026, 8, 2));

let experimentStart = DEFAULT_EXPERIMENT_START;

/** What the API said this deployment's start date is. Called once on load. */
export function setExperimentStart(isoDate: string | null | undefined): void {
  if (!isoDate) return;
  // A date-only string parses as UTC midnight, which is what a calendar date
  // needs — the same reason the journal is formatted in UTC. Parsing it as
  // local time would move it a day for every reader west of UTC.
  const parsed = new Date(`${isoDate}T00:00:00Z`);
  if (!Number.isNaN(parsed.getTime())) experimentStart = parsed;
}

/** The start date in use, whether it came from the API or the fallback. */
export function experimentStartDate(): Date {
  return experimentStart;
}

/** "2 September 2026". */
export function startedOn(): string {
  return new Intl.DateTimeFormat('en-GB', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(experimentStart);
}

/**
 * Which day of the experiment today is, counting the first as day 1.
 *
 * Counted from the start rather than from the first fill. "Day 3" should mean
 * three days of the experiment running, including the days it chose to do
 * nothing — those are results too, and a counter that only starts on the first
 * purchase hides them.
 */
export function dayNumber(now: Date = new Date()): number {
  const days = Math.floor((now.getTime() - experimentStart.getTime()) / 86_400_000);
  return Math.max(1, days + 1);
}
