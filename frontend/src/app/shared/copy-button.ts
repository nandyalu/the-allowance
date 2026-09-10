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
    this.state.set((await writeToClipboard(value)) ? 'done' : 'failed');
    setTimeout(() => this.state.set('idle'), 2000);
  }
}

/**
 * Copy text, in a secure context or not.
 *
 * **`navigator.clipboard` does not exist over plain http**, and that is the
 * normal case for this project rather than an edge one: a self-hosted copy is
 * reached at `http://192.168.x.x:8080`, which is not a secure origin, so the
 * whole Clipboard API is absent. A button that only works on the published
 * https site would be broken for everyone running their own.
 *
 * So the modern call is tried first and a textarea plus `document.exec
 * Command('copy')` catches the rest. That call is deprecated and still
 * implemented everywhere, and it is the only thing that works here.
 */
async function writeToClipboard(value: string): Promise<boolean> {
  // isSecureContext is what actually decides whether the API is there, and
  // checking it avoids a thrown promise on every insecure load.
  if (window.isSecureContext && navigator.clipboard) {
    try {
      await navigator.clipboard.writeText(value);
      return true;
    } catch {
      // A refused permission falls through to the same fallback.
    }
  }
  return legacyCopy(value);
}

/** The pre-Clipboard-API way. Deprecated, universally implemented, and the
 * only one that works on a plain-http origin. */
function legacyCopy(value: string): boolean {
  const area = document.createElement('textarea');
  area.value = value;
  // Off-screen rather than hidden: `display: none` and `visibility: hidden`
  // cannot be selected, so the copy silently produces nothing. Fixed rather
  // than absolute so a long value cannot extend the page and move the scroll.
  area.setAttribute('readonly', '');
  area.style.position = 'fixed';
  area.style.top = '0';
  area.style.left = '-9999px';
  area.style.opacity = '0';
  document.body.appendChild(area);

  const previous = document.activeElement as HTMLElement | null;
  try {
    area.select();
    // iOS ignores select() on a readonly field and needs an explicit range.
    area.setSelectionRange(0, value.length);
    return document.execCommand('copy');
  } catch {
    return false;
  } finally {
    document.body.removeChild(area);
    // Put focus back where the reader left it, so copying does not lose their
    // place on the page.
    previous?.focus?.();
  }
}
