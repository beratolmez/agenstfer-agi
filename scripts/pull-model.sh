#!/usr/bin/env sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
MODEL=${1:-qwen3.5:9b}
PROJECT_NAME=${COMPOSE_PROJECT_NAME:-agentic-growth-intelligence}
DOWNLOAD_NETWORK=${PROJECT_NAME}_model-download

case "$MODEL" in
  qwen3.5:9b|qwen3.5:27b) ;;
  *) echo "Unsupported release model: $MODEL" >&2; exit 2 ;;
esac

restore_isolation() {
  echo "Restoring the isolated Ollama network..."
  restore_status=0
  docker compose -f "$ROOT/docker-compose.yml" up -d --no-deps --force-recreate ollama || restore_status=$?
  docker network rm "$DOWNLOAD_NETWORK" >/dev/null 2>&1 || true
  if docker network inspect "$DOWNLOAD_NETWORK" >/dev/null 2>&1; then
    echo "Ollama network isolation could not be restored; stop the stack and inspect Docker networks." >&2
    restore_status=1
  fi
  return "$restore_status"
}
trap restore_isolation EXIT INT TERM

echo "Temporarily enabling outbound access for the Ollama service..."
docker compose \
  -f "$ROOT/docker-compose.yml" \
  -f "$ROOT/docker-compose.model-download.yml" \
  up -d --no-deps --force-recreate ollama
docker compose \
  -f "$ROOT/docker-compose.yml" \
  -f "$ROOT/docker-compose.model-download.yml" \
  exec -T ollama ollama pull "$MODEL"
