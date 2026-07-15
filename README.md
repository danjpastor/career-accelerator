# Career Accelerator

A local desktop application for managing a 90-day transition into data
analytics. It combines learning progress, adaptive planning, SQL
practice, portfolio development, study tracking, weekly reviews,
job-readiness evidence, applications, and Git publishing.

## Launch

On Windows, double-click:

```text
Career Accelerator.bat
```

The launcher creates a local `.venv`, installs the requirements, and
starts the application.

To create a Desktop shortcut, run:

```text
create-desktop-shortcut.vbs
```

## Current Desktop Client

Version 9.3.15 includes:

- Fixed wide reference-matched dark purple Dashboard with no scrolling
- Global hover highlights and animated click feedback for every button
- A distinct named achievement for every completed roadmap task or challenge
- Time-aware greeting that refreshes every minute
- Rotating motivational quotes and encouragement
- Functional streak, best-streak, and current-week study totals
- Selectable 7, 14, 30, or 90-day growth chart
- Adaptive planning by available time and energy
- Intelligent Today’s Focus grounded in the weekly roadmap
- Automatic promotion of up to two unfinished focus tasks from yesterday
- Visible Job Readiness and Applications workspaces
- Google, DataCamp, SQL, Power BI, Python, and portfolio tracking
- Portfolio workspace for three analytics projects
- SQL Companion with mastery and review scheduling
- Matching goal-based circular timers on Dashboard and Study Session pages
- Animated timer text/status feedback on Start, Pause, and Reset
- Current-week Weekly Summary sparkline driven only by logged sessions
- Custom Career Accelerator application and shortcut icon
- Study timer with Start, Pause, confirmed Reset, and Log Session controls
- Compact two-column Settings control center
- Future AI integration readiness status without storing credentials
- Dashboard Mission Control with live Job Readiness progress
- Persistent rewards for every completed task, milestone, SQL problem, session, and application
- Compact evidence-driven Job Readiness workspace
- Weekly summaries, achievements, charts, and streak tracking
- Job-readiness evidence and application CRM
- Local SQLite persistence, backups, and Git publishing

## Repository Structure

```text
career_app/     PySide6 application code
data/           Local SQLite database location
projects/       Portfolio project specifications and milestones
weeks/          Twelve weekly sprint plans and retrospectives
resources/      SQL, Power BI, Python, interview, and career resources
career/         Resume and LinkedIn materials
app.py           Application entry point
```

## Data

Runtime progress is stored locally in:

```text
data/career_accelerator.db
```

The database and backup directory are excluded from Git by default.
Existing progress is preserved when application files are updated.

## Keyboard Shortcuts

- `Ctrl+K` — Command palette
- `Ctrl+S` — Create a local backup

## Core Documents

- [Master Roadmap](MASTER_ROADMAP.md)
- [Current Progress](PROGRESS.md)
- [Quick Start](QUICK_START.md)
- [Contributing Workflow](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## Guiding Principle

**Learn → Apply → Document → Present**


## Windows Icon and Shortcuts

Windows does not support assigning a unique icon directly to an individual
`.bat` file. Career Accelerator therefore applies the custom icon to:

- The PySide6 application window and taskbar entry
- A repository launcher shortcut named `Career Accelerator.lnk`
- The Desktop shortcut created by `create-desktop-shortcut.vbs`

The batch launcher automatically creates the repository shortcut when it is
missing. Run `create-desktop-shortcut.vbs` to create or refresh the Desktop
shortcut.


## Starter Roadmap and Reset Progress

The factory roadmap now assumes a learner is beginning at Google Course 1,
Module 1. Learners who are already further ahead can update their current
course on the Learning page; course-specific tasks from earlier courses are
automatically recognized as complete.

**Settings → Reset All Progress** uses three confirmations, creates a safety
backup, clears all tracked progress, resets every progress date, and rebuilds
the clean starter roadmap. Technical preferences and backup files are preserved.


## Active Profile and Portfolio Checkboxes

The packaged active profile retains the Course 5 checkpoint and recognizes
documented Project 1 discovery work already present in the repository.
Factory Reset still rebuilds the clean Course 1 starter profile.

Portfolio Workspace milestones use the same high-contrast custom checkboxes
as Dashboard tasks. Clicking a milestone saves the state immediately.


## Current Google Checkpoint Task

Career Accelerator keeps one tracked task for the active Google course and
module. It receives highest Learning priority and appears in Today’s Focus
and Next Tasks until completed. Changing the course, module, or sprint
retargets and reopens it. Factory Reset creates Course 1, Module 1.


## Independent Progress Tracks

Sprint week now controls scheduling only. Google, DataCamp, SQL, and
Portfolio maintain independent checkpoints, weekly targets, and completion
histories. Their current actions feed the existing Today’s Focus, Next Tasks,
Learning cards, and SQL Companion without changing the finished layout.

See `MODULAR_TRACKS.md` for the architecture.


## Adaptive Pacing

Google certificate completion is now the primary learning objective.
Weekly targets adapt to the configured study-hour budget, and the app
calculates a daily certificate target from the remaining work and days in
the week. DataCamp and SQL are supplemental tracks aligned to the current
certificate material.

Portfolio milestones are prerequisite-gated. The planner will not suggest
a portfolio task until the necessary certificate, SQL, DataCamp, Power BI,
storytelling, or delivery skills are unlocked.

See `ADAPTIVE_PACING.md` for details.


## Final Reliability Pass

Google certificate work is always ordered first in Today’s Focus. The
adaptive engine also repairs stale track links, distinguishes locked SQL
work from completed work, unlocks skills only after their source course is
complete, and records skipped same-course modules accurately.

See `RELEASE_READINESS.md` for covered edge cases and intentional boundaries.


## Next Tasks Completion Fix

Dashboard task checkboxes now hide their row immediately and queue the
completion update until the checkbox mouse event has finished. The refreshed
task list then shows the next eligible modular task or removes an ordinary
completed sprint task.

Dynamic dashboard widgets are detached and hidden immediately during refresh
instead of remaining visible until deferred deletion occurs.


## PySide6 Checkbox Compatibility Fix

Version 9.1.3 uses the numeric `.value` property of `Qt.CheckState`
members. This fixes the `TypeError` raised by PySide6 versions that do not
permit `int(Qt.Checked)`.

The fix applies to both Dashboard Next Tasks and Portfolio Workspace
milestone checkboxes.


## Daily-Paced Next Tasks

Version 9.2.0 makes Next Tasks a daily workload rather than an endless
sequential queue.

- Completed items disappear immediately.
- The next sequential item appears only when more work is due for that track
  today.
- Daily-complete tracks return tomorrow.
- Weekly-complete tracks return the following week.
- Items already below the five-row display limit still move upward
  immediately.
- Catch-up quotas remain fixed during the day; a two-item target does not
  shrink after the first completion.
- Today's Focus follows the same pacing limits.
- Track details display `Today completed / target` and weekly progress.


## Specific Today’s Focus Labels

Version 9.2.1 replaces generic role text such as `Supplemental` with the
actual work item assigned to the track.

Examples:

- DataCamp: `Selecting columns and inspecting tables`
- SQL Practice: `Histogram of Tweets`
- Google Certificate: `Course 5, Module 1`
- Portfolio Project: `Create synthetic data specification`

Daily and weekly pacing information remains visible after the specific task
name.


## Uniform Today’s Focus Formatting

Version 9.2.2 applies one shared display rule to every Today’s Focus row:

1. The specific action appears first.
2. Daily/weekly pacing or priority appears second.
3. Course alignment is concise.
4. Duration remains exclusively in the right-hand time column.
5. The heading reflects the actual work type.

Example rows:

- `Selecting columns and inspecting tables • Today 0/1 • Week 0/2 • Supports Course 5`
- `Histogram of Tweets • Today 0/1 • Week 0/3 • Reinforces Course 5`
- `Solve Data Science Skills • Priority 1`
- `Practice SELECT, FROM, WHERE, ORDER BY, and LIMIT • Priority 3`

General sprint tasks that clearly practice SQL fundamentals are presented as
`SQL Fundamentals` without changing their stored task records or progress.


## Guided DuckDB Exercise Library

Version 9.3.0 replaces broad SQL practice reminders with twelve concrete
DuckDB assignments under `practice/duckdb/`.

Each assignment supplies a small CSV dataset, business questions, a starter
SQL file, a submission path, and result checkpoints. Completed solution SQL
is intentionally not included.

Existing databases are updated by label during normal startup. Completion
state and other progress are preserved.


## Verified DataCamp Curriculum

Version 9.3.1 replaces invented DataCamp lesson summaries with official
course and chapter names verified on July 14, 2026.

The curriculum catalog is fixed and reviewable. The app remains adaptive:
it selects the next chapter, calculates daily and weekly pacing, and hides
or advances the track based on completed work.

Daily roadmap fallbacks now read the current adaptive DataCamp, SQL, and
portfolio assignments instead of displaying separate hard-coded practice
text.


## Study Session Preservation

Version 9.3.2 prevents task completion from interrupting an active study
session.

When a task checkbox refreshes the adaptive plan, the app now preserves:

- elapsed timer time
- running or paused timer state
- session date and hours
- productivity score and SQL count
- Google, DataCamp, and portfolio notes
- unsaved session notes
- the selected session goal

Time spent while the task refresh runs is added back to a running timer.


## Working SQL Companion

Version 9.3.3 connects the problem list and workspace, creates and opens
local solution files, saves completions, and advances the adaptive SQL
track.

SQL recommendations now use title-specific concept prerequisites rather
than broad difficulty or topic labels. Problems remain hidden until every
required concept has been learned through the verified DataCamp path.


## Friday-Only Weekly Retrospectives

Version 9.3.4 keeps weekly retrospective tasks in the backlog throughout the week, but makes them eligible for Today’s Focus and Next Tasks only on Friday. Completing earlier work cannot cause the retrospective to move into a Tuesday, Wednesday, or Thursday recommendation.


## Retrospective Recovery Window

Version 9.3.5 recommends the current week's retrospective on Friday. If it
remains incomplete, the previous week's retrospective returns once on the
following Monday as `Missed Friday`.

It remains hidden on Saturday and Sunday and returns to backlog-only status
after Monday. Calendar gating applies only to retrospective deliverables;
other Review tasks continue on their normal schedule.


## Completion History and Safe Undo

Version 9.3.6 adds **Completion History / Undo** to Adaptive Planner. It
restores completed items from every week and reverses their matching
adaptive or SQL completion evidence.

SQL Companion completion now binds to the exact problem target. Completing
Histogram of Tweets may activate Solve Data Science Skills as the next
eligible task, but it cannot mark that task complete.

The release also repairs detached adaptive tasks that older versions may
have incorrectly marked complete without a matching completion record.


## Persistent Task Editing

Version 9.3.7 prevents adaptive synchronization from overwriting task edits
for the currently active assignment. Status, priority, estimated duration,
energy, and deferral now persist and are verified after saving.

The Total Estimated Time and Tasks boxes in Today’s Focus now remain compact
when fewer focus rows are displayed.


## Authoritative Task Editing

Version 9.3.8 synchronizes an adaptive task first, resolves the exact live
task row, and only then writes the values selected in the editor. The final
database values are no longer vulnerable to a legacy label or week
normalization occurring between Save and verification.

Sprint Backlog selections now use a persistent purple background, bright
left indicator, border, and bold text. The selected task remains highlighted
when buttons or dialogs receive focus and after the backlog refreshes.


## Status Restoration and Scheduling

Version 9.3.9 detects completion across the task flag, metadata status,
adaptive event, and SQL completion record. Restoring an older inconsistent
task now removes every matching completion layer before rebuilding the
adaptive schedule.

The Dashboard no longer performs a hidden second synchronization after the
editor's final write.

Sprint Backlog shows the saved status immediately. Tasks that cannot return
to the schedule because required concepts are still locked display
`🔒 Locked`, with the reason available in the tooltip and save confirmation.


## Concept Evidence and Skills Inventory

Version 9.3.10 accepts SQL evidence from DataCamp, completed Google Course 5,
guided DuckDB exercises, and concept-matched SQL problems.

Job Readiness now shows Learned, In Progress, and Locked concepts with the
evidence behind every status.


## Job Readiness Layout Repair

Version 9.3.11 makes the Job Readiness content scrollable so the new
Skills & Concepts section cannot compress the upper readiness cards.

Readiness Coach always displays guidance. Evidence Coverage rows and the
Continue Highest-Impact Task button retain usable heights instead of
rendering blank or cut off.


## DuckDB Exercise Workspace

Version 9.3.12 adds a DuckDB Exercises tab to SQL Companion. It opens the
exercise instructions, starter SQL, validation guide, datasets, and a saved
submission copy.

Exercise completion updates matching sprint tasks, contributes concept
evidence, and creates a Demonstrated Evidence entry.

Demonstrated Evidence now includes instructions, examples, validation, full
detail viewing, and clearer descriptions of what each artifact proves.


## Achievement Reconciliation

Version 9.3.13 treats achievements as derived from currently verified
progress. Restoring a task or SQL problem to unfinished removes its
task-specific achievement and recalculates threshold achievements such as
First Query and SQL Starter.

SQL readiness, dashboard progress, coaching, and weekly summaries now count
only records whose status is Completed.


## Applied Analytics Lab Library

Version 9.3.14 adds 21 guided labs covering Power BI, Excel, pandas,
communication, SQL validation, broken-analysis diagnosis, and timed analyst
requests. BigQuery is not included.

Open Learning Dashboard → Applied Labs to open resources, create saved
submissions, track progress, unlock concepts, and generate Demonstrated
Evidence.


## Branched Applied Labs Track

Version 9.3.15 adds a prerequisite-driven Applied Labs track. It chooses one
next eligible lab across the Power BI, Excel, pandas, Communication, SQL
Quality, and Timed Requests branches.

The track remains supplemental, supports automatic or pinned branch
selection, carries unfinished work across weeks, and places at most one lab
in Today’s Focus.
