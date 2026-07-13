param(
    [switch]$Live
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Push-Location $root
try {
    Write-Host "== Git status =="
    git status --short

    Write-Host "== Backend lint =="
    uv run ruff check apps/api

    Write-Host "== Backend tests =="
    uv run pytest

    Write-Host "== Migration drift =="
    uv run alembic check

    Write-Host "== Frontend tests =="
    npm --prefix apps/web test

    Write-Host "== Frontend build =="
    npm --prefix apps/web run build

    Write-Host "== Compose validation =="
    docker compose config --quiet
    docker compose -f docker-compose.yml -f docker-compose.dev.yml config --quiet
    docker compose -f docker-compose.yml -f docker-compose.cloud.yml --profile cloud config --quiet

    if ($Live) {
        Write-Host "== Live probes =="
        Invoke-RestMethod http://localhost:8080/api/health | ConvertTo-Json -Depth 8
        Invoke-RestMethod http://localhost:8080/api/setup/status | ConvertTo-Json -Depth 8
    }
}
finally {
    Pop-Location
}
