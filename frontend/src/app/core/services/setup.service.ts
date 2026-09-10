import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { SetupStatus } from '../models/api.models';

/**
 * Whether this deployment can run, and what to paste if it cannot.
 *
 * The payload carries booleans and example lines only — never a configured
 * value — so nothing here can leak a credential to a page or to the static
 * export. See backend/services/setup_check.py.
 */
/** Whether a first run should be walked to the setup page.
 *
 * A pure function rather than a method on the shell, so the rule can be read
 * and tested without a router, an outlet or a DOM.
 *
 * **Only on a first run.** A deployment that has never been switched on has
 * nothing to show and every reason to be walked through setup. One that is
 * merely failing — an LLM endpoint down for ten minutes — must not have the
 * book and the decisions yanked away mid-incident; the banner covers that on
 * every page instead.
 */
export function shouldSendToSetup(input: {
  isPublic: boolean;
  status: SetupStatus | null;
  url: string;
}): boolean {
  const { isPublic, status, url } = input;
  // A published copy is a static export with no environment to configure.
  if (isPublic) return false;
  // A status that could not be read must never claim a deployment is broken.
  if (!status) return false;
  if (!status.first_run || status.ready) return false;
  // Never bounce a reader who asked for a page on purpose — only a bare
  // landing on the root.
  return url.split('?')[0] === '/';
}

@Injectable({ providedIn: 'root' })
export class SetupService {
  private readonly http = inject(HttpClient);

  private readonly _status = signal<SetupStatus | null>(null);
  readonly status = this._status.asReadonly();

  async load(): Promise<void> {
    try {
      this._status.set(await firstValueFrom(this.http.get<SetupStatus>('/api/setup')));
    } catch {
      // A setup check that cannot be fetched must not stop the app from
      // rendering — the pages below still work, and the banner simply stays
      // hidden rather than claiming something it does not know.
      this._status.set(null);
    }
  }
}
