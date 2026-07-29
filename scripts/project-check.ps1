param(
    [switch]$Live
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

function Assert-NativeSuccess {
    param([string]$Label)
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE."
    }
}

Push-Location $root
try {
    Write-Host "== Git status =="
    git status --short
    Assert-NativeSuccess "Git status"

    Write-Host "== Backend lint =="
    uv run ruff check apps/api
    Assert-NativeSuccess "Backend lint"

    Write-Host "== Backend tests =="
    uv run pytest
    Assert-NativeSuccess "Backend tests"

    Write-Host "== Migration drift =="
    uv run alembic check
    Assert-NativeSuccess "Migration drift"

    Write-Host "== Frontend tests =="
    npm --prefix apps/web test
    Assert-NativeSuccess "Frontend tests"

    Write-Host "== Frontend build =="
    npm --prefix apps/web run build
    Assert-NativeSuccess "Frontend build"

    Write-Host "== Compose validation =="
    $baseCompose = docker compose config
    Assert-NativeSuccess "Base Compose validation"
    # The base topology always renders the variable; what must never appear is a value.
    # Strip quotes and whitespace from the value so `AGI_CLOUD_API_KEY: ""` -- the correct
    # state -- passes and only a real secret fails.
    $injectedKey = [regex]::Matches(($baseCompose -join "`n"), "(?m)^\s+AGI_CLOUD_API_KEY:\s*(.*)$") |
        ForEach-Object { $_.Groups[1].Value.Trim().Trim('"').Trim("'").Trim() } |
        Where-Object { $_ -ne "" }
    if ($injectedKey) {
        throw "Base Compose must not inject a plaintext AGI_CLOUD_API_KEY."
    }
    docker compose -f docker-compose.yml -f docker-compose.dev.yml config --quiet
    Assert-NativeSuccess "Development Compose validation"
    docker compose -f docker-compose.yml -f docker-compose.cloud.yml --profile cloud config --quiet
    Assert-NativeSuccess "Cloud Compose validation"
    docker compose -f docker-compose.yml -f docker-compose.production.yml config --quiet
    Assert-NativeSuccess "Production Compose validation"
    docker compose -f docker-compose.yml -f docker-compose.observability.yml --profile observability config --quiet
    Assert-NativeSuccess "Observability Compose validation"
    docker compose -f docker-compose.yml -f docker-compose.model-download.yml config --quiet
    Assert-NativeSuccess "Model-download Compose validation"
    docker compose -f docker-compose.yml -f docker-compose.e2e.yml config --quiet
    Assert-NativeSuccess "Browser E2E Compose validation"

    if ($Live) {
        Write-Host "== Live probes =="
        Invoke-RestMethod http://localhost:8080/api/health | ConvertTo-Json -Depth 8
        Invoke-RestMethod http://localhost:8080/api/setup/status | ConvertTo-Json -Depth 8
    }
}
finally {
    Pop-Location
}
