# Progress Automation

## What You Edit Manually

### Daily
1. Check off completed tasks in the current weekly sprint.
2. Add one row to the daily log.
3. Save each completed DataLemur solution as a `.sql` file in:
   `resources/sql/datalemur/`

### Occasionally
Update `progress-data.yml` when:
- Advancing to a new week
- Advancing to a new Google course or module
- Moving to a new portfolio project
- Changing the weekly target hours

## What Is Generated Automatically

The script updates:
- The sprint-status block in the current week
- The dashboard in the root `README.md`
- The automated summary in `PROGRESS.md`

## Local Use

From PowerShell:

```powershell
./update-progress.ps1
```

Then review and commit the generated changes.

## GitHub Actions

A push to `main` that changes weekly tasks, project tasks, SQL solution files, or `progress-data.yml` triggers the workflow.

The workflow:
1. Installs Python dependencies
2. Runs the progress generator
3. Commits generated dashboard updates when needed

## Important

GitHub repository settings must allow GitHub Actions to write to the repository:

`Settings → Actions → General → Workflow permissions → Read and write permissions`
