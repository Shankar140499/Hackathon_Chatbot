$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

Write-Host "Starting local Streamlit app from $projectRoot" -ForegroundColor Cyan
streamlit run app.py --server.address 0.0.0.0 --server.port 8501