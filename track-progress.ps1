$ErrorActionPreference = "Stop"

Write-Host "Starting Career Accelerator tracker..." -ForegroundColor Cyan

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python was not found in PATH." -ForegroundColor Red
    Write-Host "Install Python 3.10 or newer, then reopen PowerShell."
    exit 1
}

python -m pip install -r requirements.txt --quiet
python scripts/track_progress.py
