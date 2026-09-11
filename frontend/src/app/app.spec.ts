import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { SettingsService } from './core/services/settings.service';
import { SetupService, shouldSendToSetup } from './core/services/setup.service';
import { App } from './app';

/** The shell reads one thing from settings: whether this is the published copy. */
class SettingsServiceStub {
  isPublic = false;
  settings = () => ({ public: this.isPublic }) as never;
  async load(): Promise<void> {}
}

/** Whether this deployment can run, and whether it has ever been started. */
class SetupServiceStub {
  value: { ready: boolean; first_run: boolean; checks: [] } | null = {
    ready: true,
    first_run: false,
    checks: [],
  };
  status = () => this.value as never;
  async load(): Promise<void> {}
}

let settings: SettingsServiceStub;
let setup: SetupServiceStub;

interface Shell {
  drawerOpen: () => boolean;
  toggleDrawer: () => void;
  closeDrawer: () => void;
  theme: () => 'light' | 'dark';
  toggleTheme: () => void;
}

describe('App', () => {
  beforeEach(async () => {
    localStorage.clear();
    document.documentElement.removeAttribute('data-theme');
    settings = new SettingsServiceStub();
    setup = new SetupServiceStub();
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [
        provideRouter([]),
        { provide: SettingsService, useValue: settings },
        { provide: SetupService, useValue: setup },
      ],
    }).compileComponents();
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;
    expect(app).toBeTruthy();
  });

  it('should render the nav', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.brand')?.textContent).toContain('Ten Acre');
    expect(compiled.querySelector('.site-foot')).not.toBeNull();
  });

  it('reaches every page from the drawer', async () => {
    // The bottom bar on a phone only holds four links. Anything missing from
    // the drawer would be unreachable on a small screen.
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    // Every route has to be reachable without the top nav, which is hidden
    // below 52rem. The drawer is the only way in on a phone.
    const shell = fixture.componentInstance as unknown as { toggleDrawer: () => void };
    shell.toggleDrawer();
    fixture.detectChanges();

    const links = Array.from(
      (fixture.nativeElement as HTMLElement).querySelectorAll('.drawer a[href]'),
    ).map((a) => a.getAttribute('href'));

    for (const path of [
      '/',
      '/book',
      '/decisions',
      '/research',
      '/scorecard',
      '/journal',
      '/idea',
      '/method',
      '/glossary',
      '/settings',
    ]) {
      expect(links).toContain(path);
    }
  });

  it('opens and closes the drawer', async () => {
    // The drawer opens below the masthead rather than sliding over the page.
    // A panel that covers what you were reading is one you close again to
    // check where you were — so there is no scrim to dismiss any more.
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const shell = fixture.componentInstance as unknown as Shell;
    const el = fixture.nativeElement as HTMLElement;

    expect(el.querySelector('.drawer')).toBeNull();

    shell.toggleDrawer();
    fixture.detectChanges();
    expect(shell.drawerOpen()).toBe(true);
    expect(el.querySelector('.drawer')).not.toBeNull();

    shell.closeDrawer();
    fixture.detectChanges();
    expect(shell.drawerOpen()).toBe(false);
    expect(el.querySelector('.drawer')).toBeNull();
  });

  it('remembers the chosen theme', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const shell = fixture.componentInstance as unknown as Shell;

    const first = shell.theme();
    shell.toggleTheme();
    const second = shell.theme();

    expect(second).not.toBe(first);
    expect(document.documentElement.getAttribute('data-theme')).toBe(second);
    expect(localStorage.getItem('th-theme')).toBe(second);
  });

  it('drops the settings link on the published copy', async () => {
    // Presentation only. The backend refuses every write in public mode, so
    // this removes a dead end rather than closing a hole — which is why a
    // failure to load settings leaves the link showing rather than hiding it.
    settings.isPublic = true;
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const shell = fixture.componentInstance as unknown as { toggleDrawer: () => void };
    shell.toggleDrawer();
    fixture.detectChanges();

    const links = Array.from(
      (fixture.nativeElement as HTMLElement).querySelectorAll('.drawer a[href]'),
    ).map((a) => a.getAttribute('href'));

    expect(links).not.toContain('/settings');
    expect(links).toContain('/book');
  });
});

describe('first-run setup', () => {
  const bare = { ready: false, first_run: true, checks: [] };

  it('sends a never-started deployment to the setup page', () => {
    // The case the page exists for: a fresh container serves a
    // working-looking site with empty pages, and a banner is easy to miss.
    expect(shouldSendToSetup({ isPublic: false, status: bare, url: '/' })).toBe(true);
  });

  it('leaves a running deployment where it is when something breaks', () => {
    // An LLM endpoint down for ten minutes must not yank the book and the
    // decisions away mid-incident. The banner covers this case instead.
    const broken = { ready: false, first_run: false, checks: [] };
    expect(shouldSendToSetup({ isPublic: false, status: broken, url: '/' })).toBe(false);
  });

  it('does not redirect once everything is configured', () => {
    const ready = { ready: true, first_run: true, checks: [] };
    expect(shouldSendToSetup({ isPublic: false, status: ready, url: '/' })).toBe(false);
  });

  it('does not redirect on the published copy', () => {
    // A static export has no environment to configure and nothing to fix.
    expect(shouldSendToSetup({ isPublic: true, status: bare, url: '/' })).toBe(false);
  });

  it('says nothing when the setup status could not be read', () => {
    expect(shouldSendToSetup({ isPublic: false, status: null, url: '/' })).toBe(false);
  });

  it('does not bounce a reader who asked for a page on purpose', () => {
    // Only a bare landing on the root. Someone who deep-linked into the book,
    // or who navigated to setup themselves, is left alone.
    expect(shouldSendToSetup({ isPublic: false, status: bare, url: '/book' })).toBe(false);
    expect(shouldSendToSetup({ isPublic: false, status: bare, url: '/setup' })).toBe(false);
  });

  it('still fires when the root carries a query string', () => {
    expect(shouldSendToSetup({ isPublic: false, status: bare, url: '/?theme=dark' })).toBe(true);
  });
});
