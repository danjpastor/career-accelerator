# Installing Career Accelerator v10.0.1

## Upgrade an existing repository

Use `career-accelerator-v10.0.1-patch.zip`.

1. Close Career Accelerator.
2. Extract the patch ZIP.
3. Open Command Prompt or PowerShell in the extracted patch folder.
4. Run:

```text
python install_v10.py "C:\Users\Dan\Documents\GitHub\career-accelerator"
```

The installer validates the repository, skips files that already match v10.0.1, and backs up each replaced file under `patch_backups/v10.0.1-<timestamp>/`.

It does not delete the local SQLite database, backups, learner submissions, generated DuckDB data, task workspaces, or custom Exercise Packs.

## Clean installation

Use `career-accelerator-v10.0.1.zip`, extract it to a normal writable folder, and run `Career Accelerator.bat`.

The clean package does not include Git history, virtual environments, caches, local databases, backup history, learner submissions, or private task-workspace content.

## Verify the build

The application title bar and Settings status should report **10.0.1**. Resize the window down to 900×620 to verify that the Dashboard switches to a single-column compact layout and every page remains vertically scrollable without horizontal clipping.
