param(
    [ValidateSet("qwen3.5:9b", "qwen3.5:27b")]
    [string]$Model = "qwen3.5:9b"
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$base = Join-Path $root "docker-compose.yml"
$download = Join-Path $root "docker-compose.model-download.yml"

Push-Location $root
try {
    Write-Host "Temporarily enabling outbound access for the Ollama service..."
    docker compose -f $base -f $download up -d --no-deps --force-recreate ollama
    if ($LASTEXITCODE -ne 0) { throw "Could not start the model-download profile." }

    docker compose -f $base -f $download exec -T ollama ollama pull $Model
    if ($LASTEXITCODE -ne 0) { throw "Ollama could not download $Model." }
}
finally {
    Write-Host "Restoring the isolated Ollama network..."
    docker compose -f $base up -d --no-deps --force-recreate ollama
    $restoreExitCode = $LASTEXITCODE
    docker network rm agentic-growth-intelligence_model-download 2>$null | Out-Null
    $temporaryNetworkStillExists = @(
        docker network ls --filter "name=^agentic-growth-intelligence_model-download$" --format "{{.Name}}"
    ).Count -gt 0
    Pop-Location
    if ($restoreExitCode -ne 0 -or $temporaryNetworkStillExists) {
        throw "Ollama network isolation could not be restored; stop the stack and inspect Docker networks."
    }
}
