$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
Push-Location $RepoRoot

try {
    python -m pip install duckdb
    python .\practice\duckdb\setup\build_database.py
}
finally {
    Pop-Location
}
