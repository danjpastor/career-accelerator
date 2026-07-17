# SQL Companion Workflow

## Selecting a problem

A single click in the left-hand list populates the Problem Workspace
with the selected problem's title, difficulty, topic, concepts, mastery,
review date, notes, completion state, and required knowledge.

The workspace automatically selects the current adaptive SQL assignment.
After completion, it advances to the next eligible problem.

## Open My Solution

The button creates the local SQL file when necessary, then opens it in
VS Code when the `code` command is available. It falls back to the
operating system's default editor.

Solution files are stored under:

`resources/sql/datalemur/`

## Mark Complete

Completion saves mastery, review date, notes, completion date, and the
local solution path. It also updates the adaptive SQL track, Dashboard,
task list, and weekly progress.

An active Study Session is preserved during this refresh.

## Prerequisite gating

Recommendations are based on concepts completed in the verified DataCamp
chapter path. Difficulty labels do not override concept prerequisites.

For example, Histogram of Tweets is classified as Easy, but it requires
a two-stage aggregation using a subquery or CTE. It remains locked until
aggregation and CTE instruction have been completed.
