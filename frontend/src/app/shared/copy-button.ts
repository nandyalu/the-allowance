import { Component, input, signal } from '@angular/core';

/**
 * Copies a block of text, and says so.
 *
 * The prompts, answers and analyst reports on this site run to tens of
 * thousands of characters. Selecting one by dragging is a fight, and these are
 * exactly the things a reader wants to take somewhere else — into a diff, an
 * editor, another model. A publication whose claim is that the record is
 * checkable should make the record easy to lift.
 *
 * **Confirms rather than assuming.** `navigator.clipboard` needs a secure
 * context, so it is absent on a plain-http LAN address — which is how this
 * app is reached at home. A button that silently does nothing there is worse
 * than one that says it could not.
 */
@Component({
  selector: 'app-copy-button',
  template: `
    <button
      type="button"
      class="btn btn-ghost btn-sm"
      (click)="copy()"
      [attr.aria-label]="label() ? 'Copy ' + label() : 'Copy'"
    >
      {{ state() === 'idle' ? 'Copy' : state() === 'done' ? 'Copied' : 'Cannot copy' }}
    </button>
  `,
})
export class CopyButton {
  readonly text = input.required<string | null | undefined>();
  /** Names what is being copied, for a screen reader: "the prompt". */
  readonly label = input('');

  protected readonly state = signal<'idle' | 'done' | 'failed'>('idle');

  protected async copy(): Promise<void> {
    const value = this.text() ?? '';
    try {
      if (!navigator.clipboard) throw new Error('no clipboard');
      await navigator.clipboard.writeText(value);
      this.state.set('done');
    } catch {
      // http on a LAN address has no clipboard API, and a permission can be
      // refused. Say which, rather than looking broken.
      this.state.set('failed');
    }
    setTimeout(() => this.state.set('idle'), 2000);
  }
}
