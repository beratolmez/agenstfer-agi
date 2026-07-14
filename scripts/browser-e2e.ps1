param(
    [string]$BrowserChannel = "msedge"
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$files = @(
    "-f", (Join-Path $root "docker-compose.yml"),
    "-f", (Join-Path $root "docker-compose.dev.yml"),
    "-f", (Join-Path $root "docker-compose.e2e.yml")
)
$project = "agi-e2e"
$testExitCode = 1

Push-Location $root
try {
    docker compose -p $project @files down -v --remove-orphans 2>$null | Out-Null
    docker compose -p $project @files up -d --build --wait web-proxy
    if ($LASTEXITCODE -ne 0) { throw "Could not start the isolated browser E2E stack." }
    $env:E2E_BASE_URL = "http://127.0.0.1:18080"
    if ($BrowserChannel) { $env:E2E_BROWSER_CHANNEL = $BrowserChannel }
    npm --prefix apps/web run test:e2e
    $testExitCode = $LASTEXITCODE
}
finally {
    docker compose -p $project @files down -v --remove-orphans
    Remove-Item Env:E2E_BASE_URL -ErrorAction SilentlyContinue
    Remove-Item Env:E2E_BROWSER_CHANNEL -ErrorAction SilentlyContinue
    Pop-Location
}
exit $testExitCode
