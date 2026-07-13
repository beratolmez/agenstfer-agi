#!/usr/bin/env bash
set -euo pipefail

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
target="${1:-./backups/${timestamp}}"
mkdir -p "${target}"

docker compose exec -T postgres pg_dump -U "${POSTGRES_USER:-agi}" -d "${POSTGRES_DB:-agi}" -Fc > "${target}/postgres.dump"
docker run --rm -v agentic-growth-intelligence_knowledge_data:/knowledge:ro -v "$(realpath "${target}"):/backup" alpine:3.22 tar -czf /backup/knowledge.tar.gz -C /knowledge .
sha256sum "${target}/postgres.dump" "${target}/knowledge.tar.gz" > "${target}/SHA256SUMS"
echo "Backup hazır: ${target}"

