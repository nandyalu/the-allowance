import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideRouter } from '@angular/router';

import { routes } from './app.routes';
import { staticDataInterceptor } from './core/static-data.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    // A no-op on the live build (environment.staticSite is false there) — see
    // static-data.interceptor.ts for what it does on the public build.
    provideHttpClient(withInterceptors([staticDataInterceptor])),
  ],
};
