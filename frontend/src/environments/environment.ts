/** Swapped for environment.public.ts by the `public` build configuration
 * (angular.json's fileReplacements) — this is the only thing that changes
 * between the live operator build and the static public build. Everything
 * that reads `staticSite` is in static-data.interceptor.ts. */
export const environment = {
  staticSite: false,
  /** Unused here: the live build talks to its own backend. It exists so both
   * environment files have one shape, since fileReplacements swaps them. */
  snapshotRoot: '/data',
};
