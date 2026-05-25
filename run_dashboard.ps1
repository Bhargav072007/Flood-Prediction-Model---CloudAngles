$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

Write-Host "Starting local dashboard server on http://127.0.0.1:8123/" -ForegroundColor Cyan
Write-Host "Open http://127.0.0.1:8123/flood_prediction_modeling/index.html" -ForegroundColor Green

python -m http.server 8123
