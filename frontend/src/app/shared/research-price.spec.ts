import { beforeEach, describe, expect, it } from 'vitest';

import {
  DEFAULT_RESEARCH_PRICE,
  charging,
  researchPrice,
  researchPriceLabel,
  setResearchPrice,
} from './research-price';

/**
 * The site stated "$0.05" in six templates until 2026-09-10, which made every
 * deployment claim this one's charge. These tests pin the two things that fix
 * was actually about: a served price is used, and zero is a setting rather
 * than a missing value.
 */
describe('the research charge', () => {
  beforeEach(() => setResearchPrice(DEFAULT_RESEARCH_PRICE));

  it('uses what the API served', () => {
    setResearchPrice(0.25);

    expect(researchPrice()).toBe(0.25);
    expect(researchPriceLabel()).toBe('$0.25');
    expect(charging()).toBe(true);
  });

  it('treats zero as free research, not as a missing value', () => {
    // The whole reason this module exists. A `if (!usd) return` guard would
    // keep 0.05 here, and every page would name a charge this deployment does
    // not make — on exactly the deployment the fix was for.
    setResearchPrice(0);

    expect(researchPrice()).toBe(0);
    expect(charging()).toBe(false);
  });

  it('keeps the trailing zeros a price needs', () => {
    setResearchPrice(0.5);

    expect(researchPriceLabel()).toBe('$0.50');
  });

  it('ignores a missing or unusable value rather than showing NaN', () => {
    setResearchPrice(undefined);
    expect(researchPrice()).toBe(DEFAULT_RESEARCH_PRICE);

    setResearchPrice(null);
    expect(researchPrice()).toBe(DEFAULT_RESEARCH_PRICE);

    setResearchPrice(Number.NaN);
    expect(researchPrice()).toBe(DEFAULT_RESEARCH_PRICE);

    setResearchPrice(-1);
    expect(researchPrice()).toBe(DEFAULT_RESEARCH_PRICE);
  });
});
