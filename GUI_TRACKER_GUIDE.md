# Desktop GUI Tracker

The desktop tracker provides a graphical interface for routine progress updates.

## Start It

Double-click:

```text
launch-tracker.bat
```

No PowerShell command is required.

## Available Tabs

### Sprint Tasks
- View the active week's checklist
- Check or uncheck tasks
- Save all checklist changes

### Daily Log
- Record study date
- Record hours
- Record Google and DataCamp progress
- Record SQL problems completed
- Record portfolio progress

### Metadata
Update:
- Current week
- Google course
- Google module
- Current portfolio project
- Weekly target hours

### SQL Practice
- Enter a DataLemur title
- Add difficulty and concepts
- Create the correctly named `.sql` solution file automatically

### Retrospective
Add notes to:
- Wins
- Blockers
- SQL Topics to Review
- Week 2 Adjustments

## Dashboard Updates

Saving checklist changes, daily logs, metadata, or SQL files automatically refreshes:

- Root `README.md`
- `PROGRESS.md`
- Current sprint status

## After Tracking Progress

Open Git Bash, PowerShell, GitHub Desktop, or another Git client and commit the changes.

Example:

```text
progress: update current sprint
```

## Python Requirement

The GUI uses Python's built-in Tkinter interface and the existing `PyYAML` dependency.

Python 3.10 or newer is recommended.
