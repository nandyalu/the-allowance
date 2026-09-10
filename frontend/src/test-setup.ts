/**
 * What jsdom is missing that this app needs.
 *
 * **`window.matchMedia`, and it was costing eight errors a run.** Every test
 * that rendered a chart produced seven unhandled `matchMedia is not a
 * function` rejections plus one `Error: Value is null`, and Vitest warned on
 * every run that they "might cause false positive tests". They were dismissed
 * as a known quirk of `lightweight-charts` for weeks. They were not a quirk:
 * jsdom simply does not implement `matchMedia`, and two separate things here
 * call it.
 *
 * - `lightweight-charts` watches the device pixel ratio through it, to resize
 *   its canvas when a window moves between displays.
 * - `shared/chart-theme.ts`'s `watchTheme` calls it **unguarded** and then
 *   attaches a `change` listener, so every chart test was throwing on the
 *   theme path as well. That path is now actually exercised, which is the
 *   real gain here — the errors were the symptom.
 *
 * `matches: false` resolves to the light palette. A fixed answer is what a
 * test wants; a test whose result depends on the machine's colour scheme is
 * worse than one that only covers one branch.
 *
 * `app.ts` guards with `typeof matchMedia === 'function'` and does not need
 * this. It is the only caller that does, which is why the gap stayed hidden.
 */
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    // Both pairs: lightweight-charts still uses the deprecated addListener,
    // and chart-theme.ts uses the current addEventListener.
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
});
