import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';

import { AgentEvent } from '../../core/models/api.models';
import { AgentService } from '../../core/services/agent.service';
import { readerDateKey, readerDateLabel } from '../../shared/market-time';
import { DecisionCard } from './decision-card';

/** One calendar day's worth of passes, newest first, within a month. */
export interface DecisionDay {
  key: string;
  label: string;
  events: AgentEvent[];
}

/**
 * Every decision pass, grouped by month.
 *
 * The book shows what the agent holds. This shows how it decided, which is a
 * different question and the one that is hard to reconstruct later:
 * behaviour here is mostly prompt, so a month of runs across three prompt
 * revisions cannot be told apart without the words each run actually saw.
 *
 * One dot per month with a decision pass, on the timeline. The newest month
 * is expanded (and fetched) up front; every other month stays collapsed and
 * unfetched until a reader opens it — a page covering months of daily passes
 * would otherwise ship its entire history on every visit. This is why the
 * data behind it is split the same way: snapshot_export.py writes one
 * `agent_events_<YYYYMM>.json` per month, not one file with everything in it.
 */
@Component({
  selector: 'app-decisions-view',
  standalone: true,
  imports: [DecisionCard],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './decisions-view.html',
})
export class DecisionsView {
  private readonly agent = inject(AgentService);

  /** Every month with a decision pass, newest first — one dot each. */
  readonly months = signal<string[]>([]);
  readonly loadingMonths = signal(true);
  /** True when the month list itself could not be fetched. A single month
   * failing to load is tracked separately (failedMonths) — that is not the
   * whole page being down. */
  protected readonly failed = signal(false);

  private readonly eventsByMonth = signal<Map<string, AgentEvent[]>>(new Map());
  private readonly expandedMonths = signal<Set<string>>(new Set());
  private readonly loadingMonthSet = signal<Set<string>>(new Set());
  private readonly failedMonths = signal<Set<string>>(new Set());
  /** Days a reader has explicitly closed. A day's events are already fetched
   * as part of its month, so — unlike a month — there is nothing to load on
   * expand; a day defaults to open the first time its month does, and this
   * set only ever records the ones someone chose to close. */
  private readonly collapsedDays = signal<Set<string>>(new Set());

  constructor() {
    void this.agent
      .getEventMonths()
      .then((months) => {
        this.months.set(months);
        // The newest month with any data at all is treated as "current" —
        // simpler and more robust than comparing against today's calendar
        // month, which would still show an empty section on the first day
        // of a new month with nothing recorded in it yet.
        if (months.length) void this.expandMonth(months[0]);
      })
      .catch(() => this.failed.set(true))
      .finally(() => this.loadingMonths.set(false));
  }

  isExpanded(month: string): boolean {
    return this.expandedMonths().has(month);
  }

  isLoadingMonth(month: string): boolean {
    return this.loadingMonthSet().has(month);
  }

  isMonthFailed(month: string): boolean {
    return this.failedMonths().has(month);
  }

  eventsFor(month: string): AgentEvent[] {
    return this.eventsByMonth().get(month) ?? [];
  }

  /** A month's passes, split into same-day groups — newest day first, and
   * newest pass first within each day, since eventsFor() is already ordered
   * that way and grouping only ever appends into whichever day a pass
   * belongs to. */
  daysFor(month: string): DecisionDay[] {
    const groups = new Map<string, AgentEvent[]>();
    for (const event of this.eventsFor(month)) {
      const key = readerDateKey(event.ran_at);
      const events = groups.get(key);
      if (events) events.push(event);
      else groups.set(key, [event]);
    }
    return Array.from(groups, ([key, events]) => ({
      key,
      label: readerDateLabel(events[0].ran_at),
      events,
    }));
  }

  /** "2026-09" -> "September 2026". */
  monthLabel(month: string): string {
    const [year, monthNumber] = month.split('-').map(Number);
    return new Date(year, monthNumber - 1, 1).toLocaleDateString('en-US', {
      month: 'long',
      year: 'numeric',
    });
  }

  isDayExpanded(dayKey: string): boolean {
    return !this.collapsedDays().has(dayKey);
  }

  toggleDay(dayKey: string): void {
    const next = new Set(this.collapsedDays());
    next.has(dayKey) ? next.delete(dayKey) : next.add(dayKey);
    this.collapsedDays.set(next);
  }

  toggleMonth(month: string): void {
    if (this.isExpanded(month)) {
      const next = new Set(this.expandedMonths());
      next.delete(month);
      this.expandedMonths.set(next);
      return;
    }
    void this.expandMonth(month);
  }

  private async expandMonth(month: string): Promise<void> {
    const expanded = new Set(this.expandedMonths());
    expanded.add(month);
    this.expandedMonths.set(expanded);

    // Already cached from an earlier expand — nothing to fetch.
    if (this.eventsByMonth().has(month)) return;

    const loading = new Set(this.loadingMonthSet());
    loading.add(month);
    this.loadingMonthSet.set(loading);

    try {
      const events = await this.agent.getEventsForMonth(month);
      const cache = new Map(this.eventsByMonth());
      cache.set(month, events);
      this.eventsByMonth.set(cache);

      // Same "show the newest, collapse the rest" rule the months
      // themselves use, one level deeper: only the newest day in a
      // freshly-loaded month starts open. daysFor() reads eventsByMonth(),
      // which the set() above already updated, so this sees the real days.
      const days = this.daysFor(month);
      if (days.length > 1) {
        const collapsed = new Set(this.collapsedDays());
        for (const day of days.slice(1)) collapsed.add(day.key);
        this.collapsedDays.set(collapsed);
      }
    } catch {
      const failed = new Set(this.failedMonths());
      failed.add(month);
      this.failedMonths.set(failed);
    } finally {
      const done = new Set(this.loadingMonthSet());
      done.delete(month);
      this.loadingMonthSet.set(done);
    }
  }
}
