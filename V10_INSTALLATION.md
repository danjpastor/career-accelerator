# Installing Career Accelerator v10.0.0

## Upgrade an existing installation

Use `career-accelerator-v10.0.0-patch.zip`.

1. Extract the patch ZIP.
2. Close Career Accelerator.
3. Open Command Prompt or PowerShell in the extracted patch folder.
4. Run:

```text
python install_v10.py "C:\path\to\career-accelerator"
```

The installer validates the repository, skips files that already match v10.0.0, and backs up each replaced file under `patch_backups/v10.0.0-<timestamp>/`.

The installer does not delete local progress, backups, submissions, custom packs, task workspaces, or the generated DuckDB database.

## Start a clean installation

Use `career-accelerator-v10.0.0.zip`, extract it, and run `Career Accelerator.bat`.

The clean package intentionally excludes the source Git history, Python virtual environment, caches, local SQLite database, backup history, learner SQL submissions, task workspaces, and generated DuckDB database.
