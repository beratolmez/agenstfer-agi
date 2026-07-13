#!/usr/bin/env bash
set -euo pipefail

source_dir="${1:?Kullanım: scripts/restore.sh <backup-directory>}"
sha256sum -c "${source_dir}/SHA256SUMS"

docker compose exec -T postgres pg_restore --clean --if-exists -U "${POSTGRES_USER:-agi}" -d "${POSTGRES_DB:-agi}" < "${source_dir}/postgres.dump"
docker run --rm -v agentic-growth-intelligence_knowledge_data:/knowledge -v "$(realpath "${source_dir}"):/backup:ro" alpine:3.22 sh -c 'rm -rf /knowledge/* && tar -xzf /backup/knowledge.tar.gz -C /knowledge'
echo "Restore tamamlandı. app servisini yeniden başlatın."

