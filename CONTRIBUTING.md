# Repository Workflow

## Before Working

```powershell
git pull
```

Launch `Career Accelerator.bat` and make routine progress changes
through the application.

## Before Committing

1. Open **Publish & Git**.
2. Publish the progress snapshot when relevant.
3. Review the changed files.
4. Confirm that no database, backup, virtual-environment, or cache files
   are staged.

Useful commands:

```powershell
git status
git diff
git add .
git commit -m "progress: update week 1 analytics roadmap"
git push
```

## Commit Prefixes

- `app:` desktop-client changes
- `progress:` sprint and learning progress
- `sql:` SQL solutions or notes
- `project:` portfolio project work
- `career:` resume, LinkedIn, or application materials
- `docs:` documentation only
- `fix:` application bug fixes

## Repository Hygiene

Do not commit:

- `.venv/`
- `__pycache__/`
- `*.pyc`
- `data/career_accelerator.db`
- `backups/`
- credentials, tokens, or private raw datasets
