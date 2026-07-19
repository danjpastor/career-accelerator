# Undo Completion

## Location

Open **Adaptive Planner** and select **Completion History / Undo** below
the Sprint Backlog.

The dialog lists completed tasks from every roadmap week and SQL
Companion completions that may not have a visible sprint task.

## What undo reverses

- roadmap task completion state
- task metadata status
- exact adaptive track event
- SQL Companion completion status and completion date
- Google module position for the latest Google completion
- DataCamp chapter position for the latest DataCamp completion
- portfolio milestone state for the latest portfolio completion

Solution files, mastery values, review dates, and notes are preserved.

## Sequence protection

Google, DataCamp, and portfolio milestones are sequential. Only the most
recent completion in those tracks can be undone; later completions must
be undone first.

SQL problems are independent and can be undone individually.

## Exact SQL identity

SQL Companion completion now requires an exact match between:

- `problem:<title>`
- `Solve <title>`
- the selected SQL Companion title

Completing one problem can activate the next eligible task, but it
cannot mark that next task complete.
