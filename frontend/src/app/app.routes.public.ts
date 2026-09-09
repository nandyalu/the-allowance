import { Routes } from '@angular/router';

/**
 * Swapped in for app.routes.ts by the `public` build configuration
 * (angular.json's fileReplacements). Identical to app.routes.ts except the
 * `/settings` route is gone.
 *
 * Not just hidden — gone from the bundle. The live app already hides the
 * Settings nav link and the exits-arm button when `isPublic` is true, which
 * is presentation, not the boundary: on the live site the real boundary is
 * the server's write guard. The public build has no server at all, so there
 * is nothing to guard — the settings form's own code simply does not ship,
 * and `/settings` matches nothing, the same as any other unknown path.
 */
export const routes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./features/experiment/experiment-view').then((m) => m.ExperimentView),
    pathMatch: 'full',
  },
  {
    path: 'book',
    loadComponent: () => import('./features/book/book-view').then((m) => m.BookView),
  },
  {
    path: 'decisions',
    loadComponent: () => import('./features/decisions/decisions-view').then((m) => m.DecisionsView),
  },
  {
    path: 'research',
    loadComponent: () => import('./features/research/research-view').then((m) => m.ResearchView),
  },
  {
    path: 'research/ticker/:ticker',
    loadComponent: () =>
      import('./features/research/ticker-detail').then((m) => m.TickerDetailPage),
  },
  {
    path: 'research/analysis/:id',
    loadComponent: () =>
      import('./features/research/signal-detail').then((m) => m.SignalDetailPage),
  },
  {
    path: 'idea',
    loadComponent: () => import('./features/idea/idea-view').then((m) => m.IdeaView),
  },
  {
    path: 'scorecard',
    loadComponent: () => import('./features/scorecard/scorecard-view').then((m) => m.ScorecardView),
  },
  {
    path: 'method',
    loadComponent: () => import('./features/method/method-view').then((m) => m.MethodView),
  },
  {
    path: 'glossary',
    loadComponent: () => import('./features/glossary/glossary-view').then((m) => m.GlossaryView),
  },
  {
    path: 'journal',
    loadComponent: () => import('./features/journal/journal-view').then((m) => m.JournalView),
  },
  {
    path: 'preview',
    loadComponent: () => import('./features/preview/preview-view').then((m) => m.PreviewView),
  },
  // No /settings entry here — see the module docstring above.
  { path: 'agent', redirectTo: 'book' },
  { path: 'events', redirectTo: 'decisions' },
  { path: 'journey', redirectTo: 'journal' },
  { path: 'tickers', redirectTo: 'research' },
  { path: 'signals', redirectTo: 'research' },
  { path: 'tickers/:ticker', redirectTo: 'research/ticker/:ticker' },
  { path: 'signals/:id', redirectTo: 'research/analysis/:id' },
  { path: 'alerts', redirectTo: 'book' },
  { path: 'regime', redirectTo: '' },
  { path: 'digest', redirectTo: 'journal' },
  // /settings falls through to here too, same as any other unknown path.
  { path: '**', redirectTo: '' },
];
