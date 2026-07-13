# Local Progress Automation

This repository uses a local PowerShell command to update progress dashboards.

GitHub Actions are not required.

## What You Edit Manually

### After Each Study Session

1. Check off completed tasks in the current weekly sprint.
2. Add one row to the current week's daily log.
3. Save each completed DataLemur solution as a `.sql` file in:
   `resources/sql/datalemur/`

### When Progress Changes

Update `progress-data.yml` when:

- Moving to a new week
- Moving to a new Google course or module
- Starting a new portfolio project
- Changing the weekly target hours

## What the Script Updates

Running the local updater automatically refreshes:

- The current sprint status
- Weekly completion percentage
- Weekly hours
- Completed and remaining task totals
- SQL problem total
- Root README progress dashboard
- `PROGRESS.md` automated summary

## First-Time Setup

Open PowerShell in the repository root and run:

```powershell
python --version
```

Python 3.10 or newer is recommended.

Then run:

```powershell
.\update-progress.ps1
```

The script installs the required Python package and runs the progress generator.

## Normal Daily Workflow

After completing your study session:

```powershell
.\update-progress.ps1
git status
git add .
git commit -m "progress: update week 1"
git push
```

Review the generated changes before committing.

## Updating the Current Week

Edit:

```text
progress-data.yml
```

Example:

```yaml
program:
  current_week: 2
```

Then run:

```powershell
.\update-progress.ps1
```

## Troubleshooting

### PowerShell Blocks the Script

Run the script without changing your permanent policy:

```powershell
powershell -ExecutionPolicy Bypass -File .\update-progress.ps1
```

### Python Is Not Found

Install Python and select the option to add Python to PATH.

Then restart PowerShell and run:

```powershell
python --version
```

### Dashboard Does Not Change

Confirm that:

- Completed tasks use `- [x]`
- Incomplete tasks use `- [ ]`
- Daily log rows remain between the daily-log markers
- DataLemur solutions use the `.sql` extension
- `progress-data.yml` contains valid YAML
