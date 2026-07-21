# SQL Companion Workflow

## Selecting a problem

A single click in the left-hand list populates the Problem Workspace with the selected problem's title, difficulty, topic, concepts, mastery, review date, notes, completion state, and required knowledge.

The workspace automatically selects the current adaptive SQL assignment. After completion, it advances to the next eligible problem.

## Open on DataLemur

Every catalog problem has a verified, problem-specific DataLemur URL. **Open on DataLemur ↗** launches that exact question page in the default browser.

The local application remains the central workspace:

1. Open the task from Today’s Focus or Adaptive Planner.
2. SQL Companion selects the exact local problem.
3. Write and save the local SQL submission.
4. Open the official problem on DataLemur when the statement or external submission page is needed.
5. Return to SQL Companion to record notes, mastery, and completion.

## Open Submission File

The button creates the local SQL file when necessary, then opens it in VS Code when the `code` command is available. It falls back to the operating system's default editor.

Solution files are stored under:

`resources/sql/datalemur/`

## Mark Complete

Completion saves mastery, review date, notes, completion date, and the local solution path. It also updates the adaptive SQL track, Dashboard, task list, and weekly progress.

An active Study Session is preserved during this refresh.

## Prerequisite gating

Recommendations are based on verified Accelerator Academy skills and other approved concept evidence. Difficulty labels do not override concept prerequisites.

For example, Histogram of Tweets is classified as Easy, but it requires a two-stage aggregation using a subquery or CTE. It remains locked until the required concepts have been learned.
