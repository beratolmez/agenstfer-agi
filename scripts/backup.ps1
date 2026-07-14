param(
    [string]$Target = ""
)

$ErrorActionPreference = "Stop"
if (-not $Target) {
    $Target = Join-Path "backups" ([DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ"))
}
$Target = [System.IO.Path]::GetFullPath($Target)
New-Item -ItemType Directory -Path $Target -Force | Out-Null

$postgresId = (docker compose ps -q postgres).Trim()
$appId = (docker compose ps -q app).Trim()
if (-not $postgresId -or -not $appId) { throw "The postgres and app services must be running." }
$container = (docker inspect $appId | ConvertFrom-Json)[0]
$knowledgeVolume = ($container.Mounts | Where-Object Destination -eq "/data/knowledge").Name
if (-not $knowledgeVolume) { throw "Could not resolve the mounted knowledge volume." }

docker compose stop app
if ($LASTEXITCODE) { throw "Could not stop the app for a consistent backup." }
try {
    docker compose exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f /tmp/agi-postgres.dump'
    if ($LASTEXITCODE) { throw "PostgreSQL backup failed." }
    docker compose exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" -d "${POSTGRES_DB}_dbos_sys" -Fc -f /tmp/agi-dbos.dump'
    if ($LASTEXITCODE) { throw "DBOS system database backup failed." }
    docker cp "${postgresId}:/tmp/agi-postgres.dump" (Join-Path $Target "postgres.dump")
    if ($LASTEXITCODE) { throw "Could not copy the PostgreSQL backup." }
    docker cp "${postgresId}:/tmp/agi-dbos.dump" (Join-Path $Target "dbos.dump")
    if ($LASTEXITCODE) { throw "Could not copy the DBOS backup." }
    docker compose exec -T postgres rm -f /tmp/agi-postgres.dump /tmp/agi-dbos.dump
    if ($LASTEXITCODE) { throw "Could not clean temporary database backups." }
    docker run --rm -v "${knowledgeVolume}:/knowledge:ro" -v "${Target}:/backup" alpine:3.22@sha256:14358309a308569c32bdc37e2e0e9694be33a9d99e68afb0f5ff33cc1f695dce tar -czf /backup/knowledge.tar.gz -C /knowledge .
    if ($LASTEXITCODE) { throw "Knowledge backup failed." }

    $manifest = @("postgres.dump", "dbos.dump", "knowledge.tar.gz") | ForEach-Object {
        $hash = (Get-FileHash -Algorithm SHA256 (Join-Path $Target $_)).Hash.ToLowerInvariant()
        "$hash  $_"
    }
    [System.IO.File]::WriteAllLines((Join-Path $Target "SHA256SUMS"), $manifest)
}
finally {
    docker compose up -d --wait app
    if ($LASTEXITCODE) { throw "The app service could not be restarted after backup." }
}
Write-Host "Backup created at $Target"
