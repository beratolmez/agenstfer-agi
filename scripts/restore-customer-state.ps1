# Agentic Growth Intelligence (AGI) - Production Customer State Restore Script (Windows PowerShell)

param(
    [Parameter(Mandatory=$true)]
    [string]$BackupDir
)

$ErrorActionPreference = "Stop"
Write-Host "=== Starting AGI Production Restore from [$BackupDir] ===" -ForegroundColor Yellow

if (-not (Test-Path $BackupDir)) {
    throw "Backup directory does not exist: $BackupDir"
}

# 1. Restore PostgreSQL Database
$DbBackupFile = Join-Path -Path $BackupDir -ChildPath "agi_db_dump.sql"
if (Test-Path $DbBackupFile) {
    Write-Host "[1/3] Restoring PostgreSQL database..." -ForegroundColor Cyan
    Get-Content $DbBackupFile | docker compose exec -T postgres psql -U agi -d agi
    Write-Host "✓ PostgreSQL database restored." -ForegroundColor Green
} else {
    Write-Host "⚠ Database dump file missing: $DbBackupFile" -ForegroundColor Red
}

# 2. Restore OKF Knowledge Repository
$KnowledgeZip = Join-Path -Path $BackupDir -ChildPath "okf_knowledge.zip"
if (Test-Path $KnowledgeZip) {
    Write-Host "[2/3] Restoring OKF Knowledge Bundle..." -ForegroundColor Cyan
    $KnowledgeTarget = Join-Path -Path $PSScriptRoot -ChildPath "..\knowledge"
    Expand-Archive -Path $KnowledgeZip -DestinationPath $KnowledgeTarget -Force
    Write-Host "✓ OKF Knowledge bundle restored." -ForegroundColor Green
}

# 3. Restore ChromaDB Vector Store
$ChromaZip = Join-Path -Path $BackupDir -ChildPath "chroma_db.zip"
if (Test-Path $ChromaZip) {
    Write-Host "[3/3] Restoring ChromaDB Vector Store..." -ForegroundColor Cyan
    $ChromaTarget = Join-Path -Path $PSScriptRoot -ChildPath "..\chroma_db"
    Expand-Archive -Path $ChromaZip -DestinationPath $ChromaTarget -Force
    Write-Host "✓ ChromaDB vector store restored." -ForegroundColor Green
}

Write-Host "`n=== Restore Completed Successfully ===" -ForegroundColor Green
