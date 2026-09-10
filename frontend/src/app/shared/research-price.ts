/**
 * What this deployment charges the agent for one analysis.
 *
 * **Served by the API, not compiled in.** `/api/settings` carries
 * `research_price`, and `SettingsService` writes it here on load. The constant
 * below is only what to say before that arrives.
 *
 * It was written into six templates as "$0.05" until 2026-09-10, which is the
 * same fault the start date had: a value a deployment sets, stated by the site
 * as though it were a property of the software. A deployment charging nothing
 * told every reader it charged five cents.
 *
 * **Zero is a real setting, not a missing one.** `research.is_charging()` is
 * `get_price() > 0`, so free research is a supported mode — which is why the
 * copy has to change rather than print "$0.00", a figure that reads as a bug.
 * Use `charging()` to pick the sentence and `researchPrice()` to fill it.
 */

/** Five cents — the published experiment's charge, and the answer before the
 * API replies. */
export const DEFAULT_RESEARCH_PRICE = 0.05;

let price = DEFAULT_RESEARCH_PRICE;

/** What the API said this deployment charges. Called once on load. */
export function setResearchPrice(usd: number | null | undefined): void {
  // Zero is meaningful here, so this checks for a usable number rather than
  // for truthiness. `if (!usd) return` would silently keep 0.05 on exactly the
  // deployment this exists to get right.
  if (typeof usd !== 'number' || Number.isNaN(usd) || usd < 0) return;
  price = usd;
}

/** The charge in use, whether it came from the API or the fallback. */
export function researchPrice(): number {
  return price;
}

/** Whether this deployment charges at all. Mirrors `research.is_charging()`. */
export function charging(): boolean {
  return price > 0;
}

/** "$0.05", or "$0.50" — trailing zeros kept, because a price reads wrong
 * without them. */
export function researchPriceLabel(): string {
  return `$${price.toFixed(2)}`;
}
