import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { ActionResult, Settings, SettingsPatch } from '../models/api.models';
import { setExperimentStart } from '../../shared/experiment';

@Injectable({ providedIn: 'root' })
export class SettingsService {
  private readonly http = inject(HttpClient);

  private readonly _settings = signal<Settings | null>(null);
  readonly settings = this._settings.asReadonly();

  async load(): Promise<void> {
    const data = await firstValueFrom(this.http.get<Settings>('/api/settings'));
    this.apply(data);
  }

  async update(patch: SettingsPatch): Promise<void> {
    const data = await firstValueFrom(this.http.patch<Settings>('/api/settings', patch));
    this.apply(data);
  }

  /** The start date is deployment-wide rather than component state, so it is
   * pushed into shared/experiment.ts rather than read from this signal by
   * every page that says "since" or "day N". Compiled in before 2026-09-09,
   * which had a second container claiming the first one's start date. */
  private apply(data: Settings): void {
    setExperimentStart(data.experiment_start);
    this._settings.set(data);
  }
}
