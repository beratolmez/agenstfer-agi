#!/usr/bin/env bash
set -u

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
project="agi-e2e"
compose() {
  docker compose -p "${project}" \
    -f "${root}/docker-compose.yml" \
    -f "${root}/docker-compose.dev.yml" \
    -f "${root}/docker-compose.e2e.yml" \
    "$@"
}

cleanup() { compose down -v --remove-orphans >/dev/null 2>&1 || true; }
trap cleanup EXIT INT TERM
cleanup
compose up -d --build --wait web-proxy || exit 2
E2E_BASE_URL="http://127.0.0.1:18080" npm --prefix "${root}/apps/web" run test:e2e
status=$?
cleanup
trap - EXIT INT TERM
exit "${status}"
