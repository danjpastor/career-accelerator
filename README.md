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

Version 8.2.2 includes:

- Reference-matched dark purple Dashboard
- Time-aware greeting that refreshes every minute
- Adaptive planning by available time and energy
- Google, DataCamp, SQL, Power BI, Python, and portfolio tracking
- Portfolio workspace for three analytics projects
- SQL Companion with mastery and review scheduling
- Study timer with Start, Pause, and Log Session controls
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
