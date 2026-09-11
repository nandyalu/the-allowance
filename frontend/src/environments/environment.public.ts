/** Where the exported JSON lives.
 *
 * `/data` means "beside the page", which is what a Pages deployment carrying
 * both the bundle and the data gives you. That is the default because it needs
 * no setup and is what a self-hosted copy gets.
 *
 * Dockerfile.pages-publisher rewrites this line when its SNAPSHOT_BASE_URL
 * build argument is set, which points the site at an R2 bucket on its own
 * domain instead. The reason is deployment count, not speed: the bundle
 * changes about once a month and the data changes every 15 minutes, and one
 * Pages deployment carrying both made 96 deployments a day.
 */
export const environment = {
  staticSite: true,
  snapshotRoot: '/data',
};
