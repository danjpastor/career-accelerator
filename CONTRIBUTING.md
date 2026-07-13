# Workflow

## Daily

1. Pull the latest changes.
2. Complete the day's tasks.
3. Check off completed sprint items.
4. Add a row to the current week's daily log.
5. Save any SQL solution files.
6. Run the local progress updater.
7. Review generated changes.
8. Commit and push.

## Daily Commands

```powershell
git pull
.\update-progress.ps1
git status
git add .
git commit -m "progress: complete week 1 Tuesday tasks"
git push
```

## Commit Examples

- `docs: complete week 1 Monday checklist`
- `sql: add DataLemur aggregation solutions`
- `project: define VFX KPIs and stakeholders`
- `progress: complete week 1 sprint review`

## Sunday Review

Every Sunday:

- Complete the weekly retrospective
- Update qualitative wins and blockers
- Update `progress-data.yml` if the week changes
- Run `.\update-progress.ps1`
- Commit the completed sprint
