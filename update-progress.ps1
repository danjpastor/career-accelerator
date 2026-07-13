$ErrorActionPreference = "Stop"

Write-Host "Updating Career Accelerator progress..." -ForegroundColor Cyan

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python was not found in PATH." -ForegroundColor Red
    Write-Host "Install Python 3.10 or newer, then reopen PowerShell."
    exit 1
}

python -m pip install -r requirements.txt --quiet
python scripts/update_progress.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "Progress update failed." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Progress files updated successfully." -ForegroundColor Green
Write-Host "Review the changes with: git status"
