param(
    [string]$Directory = ".secrets"
)

$ErrorActionPreference = "Stop"
$Directory = [System.IO.Path]::GetFullPath($Directory)
New-Item -ItemType Directory -Path $Directory -Force | Out-Null

function New-SecureValue {
    $bytes = New-Object byte[] 48
    $generator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $generator.GetBytes($bytes) } finally { $generator.Dispose() }
    return [Convert]::ToBase64String($bytes)
}

foreach ($name in @("bootstrap_token", "session_secret", "master_key", "cloud_model_api_key")) {
    $path = Join-Path $Directory $name
    if (Test-Path -LiteralPath $path) {
        $item = Get-Item -LiteralPath $path
        if ($item.PSIsContainer) {
            Remove-Item -LiteralPath $path -Recurse -Force
            Write-Host "Removed leftover directory secret artifact: $path"
        } else {
            Write-Host "Preserved existing secret: $path"
            continue
        }
    }
    [System.IO.File]::WriteAllText($path, (New-SecureValue))
    Write-Host "Created secret: $path"
}
Write-Host "Store the bootstrap token securely; it is required only for the first admin."
