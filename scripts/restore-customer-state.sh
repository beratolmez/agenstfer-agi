#!/usr/bin/env bash
# Agentic Growth Intelligence (AGI) - Production Customer State Restore Script (Linux / macOS)

set -euo pipefail

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <path-to-backup-dir>"
    exit 1
fi

BACKUP_DIR="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Starting AGI Production Restore from [${BACKUP_DIR}] ==="

if [ ! -d "${BACKUP_DIR}" ]; then
    echo "Error: Backup directory does not exist: ${BACKUP_DIR}"
    exit 1
fi

# 1. Restore PostgreSQL Database
if [ -f "${BACKUP_DIR}/agi_db_dump.sql" ]; then
    echo "[1/3] Restoring PostgreSQL database..."
    docker compose exec -T postgres psql -U agi -d agi < "${BACKUP_DIR}/agi_db_dump.sql"
    echo "✓ PostgreSQL database restored."
fi

# 2. Restore OKF Knowledge Bundle
if [ -f "${BACKUP_DIR}/okf_knowledge.tar.gz" ]; then
    echo "[2/3] Restoring OKF Knowledge Bundle..."
    tar -xzf "${BACKUP_DIR}/okf_knowledge.tar.gz" -C "${SCRIPT_DIR}/.."
    echo "✓ OKF Knowledge bundle restored."
fi

# 3. Restore ChromaDB Vector Store
if [ -f "${BACKUP_DIR}/chroma_db.tar.gz" ]; then
    echo "[3/3] Restoring ChromaDB Vector Store..."
    tar -xzf "${BACKUP_DIR}/chroma_db.tar.gz" -C "${SCRIPT_DIR}/.."
    echo "✓ ChromaDB vector store restored."
fi

echo ""
echo "=== Restore Completed Successfully ==="
