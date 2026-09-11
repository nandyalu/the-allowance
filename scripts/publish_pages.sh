#!/bin/sh
# Publishes the static public site to Cloudflare Pages, on a loop.
#
# Combines the pre-built Angular shell (baked into this image at build time —
# it changes only on a redeploy of this container) with the exporter's JSON
# files (baked nowhere — read fresh from the shared volume every round, since
# backend/services/snapshot_export.py rewrites them every 15 minutes). Never
# runs on a schedule of its own choosing: PUBLISH_INTERVAL_SECONDS matches
# that same 15 minutes by default, so a round here always has fresh data
# waiting, not a stale copy from the round before.
set -eu

PROJECT_NAME="${PAGES_PROJECT_NAME:-ten-acre}"
DATA_DIR="/data/public_snapshot"
SITE_DIR="./site"
COMBINED_DIR="/tmp/combined"
INTERVAL="${PUBLISH_INTERVAL_SECONDS:-900}"

if [ -z "${CLOUDFLARE_API_TOKEN:-}" ] || [ -z "${CLOUDFLARE_ACCOUNT_ID:-}" ]; then
  echo "CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID must both be set — refusing to start." >&2
  exit 1
fi

# One-time and idempotent. wrangler pages deploy does not create a project on
# its own — this fails harmlessly ("already exists") on every run after the
# first, which is simpler than tracking whether it has run before.
npx --yes wrangler@4.130.0 pages project create "$PROJECT_NAME" --production-branch=main || true

while true; do
  rm -rf "$COMBINED_DIR"
  mkdir -p "$COMBINED_DIR"
  cp -r "$SITE_DIR/." "$COMBINED_DIR/"

  if [ -d "$DATA_DIR" ]; then
    mkdir -p "$COMBINED_DIR/data"
    cp -r "$DATA_DIR/." "$COMBINED_DIR/data/"
  else
    # Not an error on a fresh deployment: the exporter's first run may not
    # have landed yet. Publish the app shell anyway rather than blocking on
    # it — every page already handles a fetch that comes back empty.
    echo "No exported data yet at $DATA_DIR — publishing the app shell without it."
  fi

  if npx --yes wrangler@4.130.0 pages deploy "$COMBINED_DIR" \
      --project-name="$PROJECT_NAME" --branch=main --commit-dirty=true; then
    echo "Published. Next check in ${INTERVAL}s."
  else
    echo "Publish failed this round — will retry in ${INTERVAL}s." >&2
  fi

  sleep "$INTERVAL"
done
