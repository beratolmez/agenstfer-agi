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
docker compose config --quiet
docker compose -f docker-compose.yml -f docker-compose.dev.yml config --quiet
docker compose -f docker-compose.yml -f docker-compose.cloud.yml --profile cloud config --quiet
docker compose -f docker-compose.yml -f docker-compose.production.yml config --quiet
docker compose -f docker-compose.yml -f docker-compose.observability.yml --profile observability config --quiet
docker compose -f docker-compose.yml -f docker-compose.model-download.yml config --quiet

if [[ "${1:-}" == "--live" ]]; then
  echo "== Live probes =="
  curl --fail --silent --show-error http://localhost:8080/api/health
  echo
  curl --fail --silent --show-error http://localhost:8080/api/setup/status
  echo
fi
