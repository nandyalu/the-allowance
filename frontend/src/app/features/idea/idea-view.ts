import { Component, computed, inject } from '@angular/core';

import { Logo } from '../../shared/logo';
import { startedOn } from '../../shared/experiment';
import { charging, researchPriceLabel } from '../../shared/research-price';
import { SettingsService } from '../../core/services/settings.service';

/**
 * Why this exists, who built it, and what did not work.
 *
 * **The draft is Claude's; the voice has to be nandyalu's.** Everything here is
 * assembled from CLAUDE.md, the journal and the benchmark write-ups, which
 * means it is accurate and it is not personal. The page is marked as a draft
 * until that is fixed, because a first-person story written by someone else is
 * the one thing on this site that would be dishonest.
 *
 * The second half is the part that earns trust with a technical reader: what
 * was tried, what failed, and what it cost. Publishing the failures is what
 * separates an experiment from a product page.
 */
@Component({
  selector: 'app-idea-view',
  imports: [Logo],
  templateUrl: './idea-view.html',
})
export class IdeaView {
  private readonly settings = inject(SettingsService);

  /** The charge this deployment actually makes, and whether it makes one.
   * Written into the template as "$0.05" until 2026-09-10. */
  protected readonly researchPriceLabel = researchPriceLabel;
  protected readonly charging = charging;

  /** This deployment's allowance, not the published one's $10,000. Whole
   * dollars: the page is prose, and a budget is always a round number. The
   * settings load is already in flight from the app shell, so this shows the
   * default for the first paint and settles once it lands. */
  protected readonly budget = computed(() => {
    const value = this.settings.settings()?.agent_budget ?? 10000;
    return `$${value.toLocaleString('en-US', { maximumFractionDigits: 0 })}`;
  });
  /** When THIS deployment started, not when the published one did. The date
   * was written into the template, so every self-hosted copy claimed to have
   * begun on the day this experiment began. */
  protected readonly startedOn = startedOn;
}
