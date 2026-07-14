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

Version 9.1.1 includes:

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
