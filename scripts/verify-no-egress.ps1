$ErrorActionPreference = "Stop"
$appId = (docker compose ps -q app).Trim()
if (-not $appId) { throw "The app service must be running." }
$ErrorActionPreference = "Continue"
docker exec $appId python -c "import urllib.request; urllib.request.urlopen('https://example.com', timeout=3)" 2>&1 | Out-Null
$egressExitCode = $LASTEXITCODE
$ErrorActionPreference = "Stop"
if ($egressExitCode -eq 0) { throw "Unexpected external network access from the app container." }
Write-Host "Default app network correctly blocks external egress."
