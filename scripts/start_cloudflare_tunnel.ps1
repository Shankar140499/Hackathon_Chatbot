$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$toolsDir = Join-Path $projectRoot "tools"
$cloudflaredExe = Join-Path $toolsDir "cloudflared.exe"

New-Item -ItemType Directory -Path $toolsDir -Force | Out-Null

if (-not (Test-Path $cloudflaredExe)) {
    Write-Host "Downloading cloudflared..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" -OutFile $cloudflaredExe
}

Write-Host "Starting public tunnel to http://localhost:8501" -ForegroundColor Cyan
& $cloudflaredExe tunnel --url http://localhost:8501