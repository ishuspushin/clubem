# Run from project root:
#   Set-ExecutionPolicy -Scope Process Bypass
#   .\scripts\dev_run.ps1

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = (Join-Path $ProjectRoot "src")

# Create folders (safe if already exist)
New-Item -ItemType Directory -Force -Path "data\uploads","data\outputs","data\jobs","schema_registry\active","schema_registry\history" | Out-Null

Write-Host "Starting worker in background..."
$worker = Start-Process -FilePath "poetry" `
  -ArgumentList @("run","python","scripts\run_worker.py") `
  -PassThru

try {
  Write-Host "Starting Flask API (foreground)..."
  # Keep API in the current console so logs are visible
  & poetry run python scripts\run_flask_dev.py
}
finally {
  Write-Host "Stopping worker (pid=$($worker.Id))..."
  try { Stop-Process -Id $worker.Id -Force } catch { }
}
