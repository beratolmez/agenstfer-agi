# Agentic Growth Intelligence (AGI) - Production Customer State Backup Script (Windows PowerShell)

$ErrorActionPreference = "Stop"
$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$BackupDir = Join-Path -Path $PSScriptRoot -ChildPath "..\backups\agi-backup-$Timestamp"

New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
Write-Host "=== Starting AGI Production Backup [$Timestamp] ===" -ForegroundColor Green

# 1. Backup PostgreSQL Database
Write-Host "[1/3] Dumping PostgreSQL database..." -ForegroundColor Cyan
$DbBackupFile = Join-Path -Path $BackupDir -ChildPath "agi_db_dump.sql"
docker compose exec -T postgres pg_dump -U agi -d agi > $DbBackupFile
Write-Host "✓ Database dumped to $DbBackupFile" -ForegroundColor Green

# 2. Backup OKF Knowledge Git Repository
Write-Host "[2/3] Archiving OKF Knowledge Repository..." -ForegroundColor Cyan
$KnowledgeSource = Join-Path -Path $PSScriptRoot -ChildPath "..\knowledge"
$KnowledgeZip = Join-Path -Path $BackupDir -ChildPath "okf_knowledge.zip"
Compress-Archive -Path "$KnowledgeSource\*" -DestinationPath $KnowledgeZip -Force
Write-Host "✓ OKF Knowledge bundle archived to $KnowledgeZip" -ForegroundColor Green

# 3. Backup ChromaDB Vector Store Snapshot
Write-Host "[3/3] Archiving ChromaDB Vector Indexes..." -ForegroundColor Cyan
$ChromaSource = Join-Path -Path $PSScriptRoot -ChildPath "..\chroma_db"
if (Test-Path $ChromaSource) {
    $ChromaZip = Join-Path -Path $BackupDir -ChildPath "chroma_db.zip"
    Compress-Archive -Path "$ChromaSource\*" -DestinationPath $ChromaZip -Force
    Write-Host "✓ ChromaDB vector store archived to $ChromaZip" -ForegroundColor Green
} else {
    Write-Host "⚠ ChromaDB folder not found; skipping." -ForegroundColor Yellow
}

Write-Host "`n=== Backup Completed Successfully ===" -ForegroundColor Green
Write-Host "Backup Location: $BackupDir" -ForegroundColor White
