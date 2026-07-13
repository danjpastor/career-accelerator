# Interactive Progress Tracker

The tracker provides a menu so you do not need to edit most tracking files manually.

## Start the Tracker

Open PowerShell in the repository root and run:

```powershell
.\track-progress.ps1
```

If PowerShell blocks the script:

```powershell
powershell -ExecutionPolicy Bypass -File .\track-progress.ps1
```

## Menu Options

### 1. View Current Checklist
Displays every checkbox in the active weekly sprint.

### 2. Mark or Reopen Checklist Tasks
Enter task numbers such as:

```text
1,3,5
```

The tracker toggles those tasks and refreshes all dashboards.

### 3. Add Daily Study Log
Prompts for:

- Date
- Hours studied
- Google progress
- DataCamp progress
- Number of SQL problems
- Portfolio progress

The row is inserted into the active sprint automatically.

### 4. Create DataLemur Solution File
Creates a correctly named `.sql` file in:

```text
resources/sql/datalemur/
```

This also increases the automated SQL total.

### 5. Update Metadata
Updates:

- Current week
- Google course
- Google module
- Current portfolio project
- Weekly target hours

### 6. Add Retrospective Note
Adds a note to the current week's retrospective file.

### 7. Refresh Dashboards
Runs the existing progress generator manually.

## Recommended Daily Routine

1. Run `.\track-progress.ps1`
2. Mark completed tasks
3. Add the daily study log
4. Create SQL solution stubs as needed
5. Exit
6. Review changes:

```powershell
git status
git diff
```

7. Commit and push:

```powershell
git add .
git commit -m "progress: update current sprint"
git push
```
