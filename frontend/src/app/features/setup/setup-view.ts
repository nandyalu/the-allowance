import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';
import { RouterLink } from '@angular/router';

import { SetupCheck } from '../../core/models/api.models';
import { SetupService } from '../../core/services/setup.service';

/**
 * What this deployment still needs before it can run.
 *
 * Everything here was configured through environment variables a self-hoster
 * found by reading documentation, and everything that went wrong said so only
 * in a log line nobody was watching. A container came up looking healthy,
 * placed no orders, and the reason was one `docker logs` away.
 *
 * **It teaches; it does not store.** Every secret and every guard stays in the
 * environment: a credential in the database is one careless serialisation away
 * from the public static export, and a guard the app can rewrite from a
 * browser is not a guard. So this page shows the exact lines to paste and says
 * to restart.
 */
@Component({
  selector: 'app-setup-view',
  standalone: true,
  imports: [RouterLink],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './setup-view.html',
})
export class SetupView {
  private readonly setup = inject(SetupService);

  readonly status = this.setup.status;

  /** Blocking first, which is the order a person fixes them in. */
  readonly blocking = computed(() => this.checks().filter((c) => c.blocking));
  readonly optional = computed(() => this.checks().filter((c) => !c.blocking));

  readonly outstanding = computed(() => this.blocking().filter((c) => !c.ready).length);

  constructor() {
    void this.setup.load();
  }

  private checks(): SetupCheck[] {
    return this.status()?.checks ?? [];
  }
}
