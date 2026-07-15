param(
    [Parameter(Mandatory = $true)]
    [string]$BaseUrl,
    [Parameter(Mandatory = $true)]
    [string]$AdminEmail,
    [ValidateSet("local-balanced", "local-strong", "cloud-balanced")]
    [string]$ModelProfile = "local-balanced",
    [ValidateRange(1, 180)]
    [int]$TimeoutMinutes = 60,
    [string]$BrowserChannel = "msedge",
    [switch]$ConfirmDisposable
)

$ErrorActionPreference = "Stop"
if (-not $ConfirmDisposable) {
    throw "Pass -ConfirmDisposable. This release test creates users, data, runs, approvals, and an active OKF revision."
}
if (-not $env:AGI_E2E_ADMIN_PASSWORD) {
    throw "Set AGI_E2E_ADMIN_PASSWORD in the process environment; secrets are not accepted as command-line arguments."
}
$uri = [Uri]$BaseUrl
$loopback = $uri.Host -in @("localhost", "127.0.0.1", "::1")
if ($uri.Scheme -ne "https" -and -not $loopback) {
    throw "Use HTTPS for non-loopback release targets."
}
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$previous = @{}
$variables = @(
    "AGI_E2E_REAL_MODEL", "AGI_E2E_CONFIRM_DISPOSABLE", "AGI_E2E_ADMIN_EMAIL",
    "AGI_E2E_ADMIN_PASSWORD", "AGI_E2E_BOOTSTRAP_TOKEN", "AGI_E2E_MODEL_PROFILE",
    "AGI_E2E_TIMEOUT_MS", "E2E_BASE_URL", "E2E_BROWSER_CHANNEL"
)
foreach ($name in $variables) { $previous[$name] = [Environment]::GetEnvironmentVariable($name, "Process") }

try {
    $env:AGI_E2E_REAL_MODEL = "true"
    $env:AGI_E2E_CONFIRM_DISPOSABLE = "true"
    $env:AGI_E2E_ADMIN_EMAIL = $AdminEmail
    $env:AGI_E2E_MODEL_PROFILE = $ModelProfile
    $env:AGI_E2E_TIMEOUT_MS = [string]($TimeoutMinutes * 60 * 1000)
    $env:E2E_BASE_URL = $BaseUrl.TrimEnd("/")
    if ($BrowserChannel) { $env:E2E_BROWSER_CHANNEL = $BrowserChannel }
    Push-Location (Join-Path $root "apps\web")
    try {
        npx playwright test e2e/real-model-happy-path.spec.ts
        if ($LASTEXITCODE -ne 0) { throw "Real-model browser E2E failed with exit code $LASTEXITCODE." }
    }
    finally { Pop-Location }
}
finally {
    foreach ($name in $variables) {
        [Environment]::SetEnvironmentVariable($name, $previous[$name], "Process")
    }
}
