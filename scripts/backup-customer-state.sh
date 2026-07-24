#!/usr/bin/env bash
# Agentic Growth Intelligence (AGI) - Production Customer State Backup Script (Linux / macOS)

set -euo pipefail

TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${SCRIPT_DIR}/../backups/agi-backup-${TIMESTAMP}"

mkdir -p "${BACKUP_DIR}"
echo "=== Starting AGI Production Backup [${TIMESTAMP}] ==="

# 1. Backup PostgreSQL Database
echo "[1/3] Dumping PostgreSQL database..."
docker compose exec -T postgres pg_dump -U agi -d agi > "${BACKUP_DIR}/agi_db_dump.sql"
echo "✓ Database dumped to ${BACKUP_DIR}/agi_db_dump.sql"

# 2. Backup OKF Knowledge Git Repository
echo "[2/3] Archiving OKF Knowledge Repository..."
tar -czf "${BACKUP_DIR}/okf_knowledge.tar.gz" -C "${SCRIPT_DIR}/.." knowledge/
echo "✓ OKF Knowledge bundle archived to ${BACKUP_DIR}/okf_knowledge.tar.gz"

# 3. Backup ChromaDB Vector Store Snapshot
echo "[3/3] Archiving ChromaDB Vector Indexes..."
if [ -d "${SCRIPT_DIR}/../chroma_db" ]; then
  tar -czf "${BACKUP_DIR}/chroma_db.tar.gz" -C "${SCRIPT_DIR}/.." chroma_db/
  echo "✓ ChromaDB vector store archived to ${BACKUP_DIR}/chroma_db.tar.gz"
fi

echo ""
echo "=== Backup Completed Successfully ==="
echo "Backup Location: ${BACKUP_DIR}"
