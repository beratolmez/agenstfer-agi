param(
    [ValidateSet("local-balanced", "local-strong", "cloud-balanced")]
    [string]$Profile = "local-balanced",
    [ValidateRange(1, 100)]
    [int]$Attempts = 20
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$reportName = "evaluation-$Profile.json"
$hostOutput = Join-Path $root "artifacts\release\$reportName"

Push-Location $root
try {
    docker compose exec -T app python scripts/run-golden-eval.py `
        --profile $Profile `
        --attempts $Attempts `
        --output "/tmp/$reportName"
    $evaluationExitCode = $LASTEXITCODE

    New-Item -ItemType Directory -Force (Split-Path $hostOutput) | Out-Null
    docker compose cp "app:/tmp/$reportName" $hostOutput
    if ($LASTEXITCODE -ne 0) { throw "Could not copy the model qualification report." }
    Write-Host "Qualification report: $hostOutput"
    exit $evaluationExitCode
}
finally {
    Pop-Location
}
