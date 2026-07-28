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
# The golden-evaluation harness this script used to invoke was built on the removed
# legacy stack (chromadb + apps/services/ai-agent) and never shipped inside the image,
# so this gate has not actually run for some time. It must be rebuilt on
# agi_server.evaluation so that it is packaged with the application.
Write-Error "model qualification harness is not available: rebuild it on agi_server.evaluation"
Write-Error "see docs/REMEDIATION_ROADMAP.md (model qualification harness)"
exit 3

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
