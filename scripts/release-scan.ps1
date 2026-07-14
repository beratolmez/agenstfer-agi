param(
    [string]$Image = "agentic-growth-intelligence-app:latest",
    [string]$OutputDirectory = "artifacts/release"
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$OutputDirectory = [System.IO.Path]::GetFullPath((Join-Path $root $OutputDirectory))
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null

docker image inspect $Image | Out-Null
if ($LASTEXITCODE) { throw "Build the release image before scanning: docker compose build app" }
# Docker Scout's local mode avoids a registry lookup and works without Docker Hub login.
docker scout sbom "local://$Image" --format cyclonedx --output (Join-Path $OutputDirectory "sbom.cdx.json")
if ($LASTEXITCODE) { throw "SBOM generation failed." }

$trivy = "aquasec/trivy:0.71.2@sha256:f5d0e600ecda7449e2a9b272805aef698631d3bb3f3a739a750de2c6819acdc9"
docker run --rm `
    -v /var/run/docker.sock:/var/run/docker.sock `
    -v trivy_cache:/root/.cache `
    -v "${OutputDirectory}:/reports" `
    $trivy image `
    --skip-version-check `
    --scanners vuln,secret `
    --severity HIGH,CRITICAL `
    --ignore-unfixed `
    --exit-code 1 `
    --format json `
    --output /reports/trivy.json `
    $Image
if ($LASTEXITCODE) { throw "Fixable high/critical vulnerability or secret finding detected." }
$report = Get-Content (Join-Path $OutputDirectory "trivy.json") -Raw | ConvertFrom-Json
$secretFindings = @(
    $report.Results |
        ForEach-Object { @($_.Secrets) } |
        Where-Object { $_ }
)
if ($secretFindings.Count -gt 0) {
    throw "Trivy reported $($secretFindings.Count) secret finding(s)."
}
Write-Host "Release reports written to $OutputDirectory"
