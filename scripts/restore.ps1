param(
    [Parameter(Mandatory = $true)]
    [string]$SourceDirectory
)

$ErrorActionPreference = "Stop"
$SourceDirectory = [System.IO.Path]::GetFullPath($SourceDirectory)
$manifestPath = Join-Path $SourceDirectory "SHA256SUMS"
if (-not (Test-Path -LiteralPath $manifestPath)) { throw "SHA256SUMS is missing." }

$expectedFiles = @("postgres.dump", "knowledge.tar.gz")
$seenFiles = @{}
foreach ($line in Get-Content -LiteralPath $manifestPath) {
    if ($line -notmatch '^([0-9a-fA-F]{64})\s+(.+)$') { throw "Invalid checksum manifest." }
    $fileName = $Matches[2]
    if ($fileName -notin $expectedFiles -or $seenFiles.ContainsKey($fileName)) {
        throw "Unexpected or duplicate checksum entry: $fileName"
    }
    $seenFiles[$fileName] = $true
    $path = Join-Path $SourceDirectory $fileName
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash
    if ($actual -ne $Matches[1]) { throw "Checksum mismatch for $fileName." }
}
if ($seenFiles.Count -ne $expectedFiles.Count) { throw "Checksum manifest is incomplete." }
$unsafe = docker run --rm -v "${SourceDirectory}:/backup:ro" alpine:3.22@sha256:14358309a308569c32bdc37e2e0e9694be33a9d99e68afb0f5ff33cc1f695dce sh -c "tar -tzf /backup/knowledge.tar.gz | grep -E '(^/|(^|/)\.\.(/|$))' || true"
if ($unsafe) { throw "Unsafe path detected in knowledge archive." }
$unsafeType = docker run --rm -v "${SourceDirectory}:/backup:ro" alpine:3.22@sha256:14358309a308569c32bdc37e2e0e9694be33a9d99e68afb0f5ff33cc1f695dce sh -c "tar -tvzf /backup/knowledge.tar.gz | awk '`$1 !~ /^[d-]/ {print}'"
if ($unsafeType) { throw "Symlink or special entry detected in knowledge archive." }

$postgresId = (docker compose ps -q postgres).Trim()
$appId = (docker compose ps -q app).Trim()
if (-not $postgresId -or -not $appId) { throw "The postgres and app services must be running." }
$container = (docker inspect $appId | ConvertFrom-Json)[0]
$knowledgeVolume = ($container.Mounts | Where-Object Destination -eq "/data/knowledge").Name
if (-not $knowledgeVolume) { throw "Could not resolve the mounted knowledge volume." }

function Start-OriginalApp {
    docker start $appId | Out-Null
    if ($LASTEXITCODE) { throw "The original app container could not be restarted." }
    for ($attempt = 0; $attempt -lt 60; $attempt++) {
        $state = (docker inspect $appId | ConvertFrom-Json)[0].State
        $status = if ($state.Health) { $state.Health.Status } else { $state.Status }
        if ($status -in @("healthy", "running")) { return }
        if ($status -in @("unhealthy", "exited", "dead")) {
            throw "The original app container entered state '$status'."
        }
        Start-Sleep -Seconds 2
    }
    throw "The original app container did not become healthy in time."
}

docker compose stop app
if ($LASTEXITCODE) { throw "Could not stop the app service." }
try {
    docker cp (Join-Path $SourceDirectory "postgres.dump") "${postgresId}:/tmp/agi-postgres.dump"
    if ($LASTEXITCODE) { throw "Could not stage the PostgreSQL backup." }
    docker compose exec -T postgres sh -c 'pg_restore --clean --if-exists -U "$POSTGRES_USER" -d "$POSTGRES_DB" /tmp/agi-postgres.dump'
    if ($LASTEXITCODE) { throw "PostgreSQL restore failed." }
    docker compose exec -T postgres rm -f /tmp/agi-postgres.dump
    if ($LASTEXITCODE) { throw "Could not clean staged database backup." }
    docker run --rm -v "${knowledgeVolume}:/knowledge" -v "${SourceDirectory}:/backup:ro" alpine:3.22@sha256:14358309a308569c32bdc37e2e0e9694be33a9d99e68afb0f5ff33cc1f695dce sh -c 'find /knowledge -mindepth 1 -maxdepth 1 -exec rm -rf -- {} + && tar -xzf /backup/knowledge.tar.gz -C /knowledge'
    if ($LASTEXITCODE) { throw "Knowledge restore failed." }
}
finally {
    Start-OriginalApp
}
Write-Host "Restore completed and the app service was restarted."
