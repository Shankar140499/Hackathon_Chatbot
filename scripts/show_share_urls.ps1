$ErrorActionPreference = "Stop"

$localUrl = "http://localhost:8501"
$ipAddresses = Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object {
        $_.IPAddress -match '^(?:\d{1,3}\.){3}\d{1,3}$' -and
        $_.IPAddress -notlike "127.*" -and
        $_.IPAddress -notlike "169.254.*" -and
        $_.PrefixOrigin -ne "WellKnown" -and
        $_.ValidLifetime -ne ([TimeSpan]::Zero)
    } |
    Select-Object -ExpandProperty IPAddress -Unique

Write-Host "Local URL: $localUrl" -ForegroundColor Cyan

if (-not $ipAddresses) {
    Write-Host "No LAN IPv4 address detected." -ForegroundColor Yellow
    exit 0
}

Write-Host "LAN share URLs:" -ForegroundColor Cyan
foreach ($ipAddress in $ipAddresses) {
    Write-Host "http://$ipAddress:8501" -ForegroundColor Green
}