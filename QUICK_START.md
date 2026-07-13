# Quick Start

## Begin a Study Session

Open the current sprint:

```text
weeks/week-01/README.md
```

Complete the assigned tasks.

## Log Progress

- Change completed tasks from `[ ]` to `[x]`
- Add one row to the daily log
- Save completed SQL practice files in `resources/sql/datalemur/`

## Update Dashboards

Run:

```powershell
.\update-progress.ps1
```

## Commit Progress

```powershell
git add .
git commit -m "progress: update current sprint"
git push
```

## End the Week

1. Complete the sprint retrospective.
2. Update `PROGRESS.md` with wins and blockers.
3. Change `program.current_week` in `progress-data.yml`.
4. Run the updater.
5. Commit and push.
