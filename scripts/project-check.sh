#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${root}"

echo "== Git status =="
git status --short
echo "== Backend lint =="
uv run ruff check apps/api
echo "== Backend tests =="
uv run pytest
echo "== Migration drift =="
uv run alembic check
echo "== Frontend tests =="
npm --prefix apps/web test
echo "== Frontend build =="
npm --prefix apps/web run build
echo "== Compose validation =="
base_compose="$(docker compose config)"
# The base topology always renders the variable; what must never appear is a value.
# Match the value and strip quotes and whitespace, so `AGI_CLOUD_API_KEY: ""` -- the
# correct state -- passes and only a real secret fails.
injected_key="$(sed -nE 's/^[[:space:]]+AGI_CLOUD_API_KEY:[[:space:]]*//p' <<<"${base_compose}" \
  | tr -d "\"' \t\r")"
if [[ -n "${injected_key}" ]]; then
  echo "Base Compose must not inject a plaintext AGI_CLOUD_API_KEY." >&2
  exit 1
fi
docker compose -f docker-compose.yml -f docker-compose.dev.yml config --quiet
docker compose -f docker-compose.yml -f docker-compose.cloud.yml --profile cloud config --quiet
docker compose -f docker-compose.yml -f docker-compose.production.yml config --quiet
docker compose -f docker-compose.yml -f docker-compose.observability.yml --profile observability config --quiet
docker compose -f docker-compose.yml -f docker-compose.model-download.yml config --quiet
docker compose -f docker-compose.yml -f docker-compose.e2e.yml config --quiet

if [[ "${1:-}" == "--live" ]]; then
  echo "== Live probes =="
  curl --fail --silent --show-error http://localhost:8080/api/health
  echo
  curl --fail --silent --show-error http://localhost:8080/api/setup/status
  echo
fi
