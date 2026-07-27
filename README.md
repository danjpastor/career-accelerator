# Data Career Accelerator

A local Windows desktop application for completing a structured 90-day transition into data analytics. It combines guided learning, adaptive daily planning, SQL practice, portfolio development, study tracking, job-readiness evidence, applications, and Git publishing.

## Current version

**v10.31.0**

This release simplifies Spreadsheet Academy around one continuing Google Sheets workbook, repairs the Dashboard Next Tasks scroll range, and removes retired patch, backup, Exercise Pack, cache, and documentation artifacts.

## Launch

Double-click:

```text
Career Accelerator.bat
```

The launcher creates or repairs the local `.venv`, installs the required packages, and starts the application. Run `create-desktop-shortcut.vbs` to create or refresh the Desktop shortcut.

## Spreadsheet Academy

Spreadsheet Academy teaches spreadsheet analysis in Google Sheets using the continuing **Northstar Operations Practice Workbook**.

One-time setup:

1. Select **Get Starter Workbook** in a spreadsheet lesson.
2. Import the `.xlsx` file into Google Sheets as a new spreadsheet.
3. Set **Share → General access** to **Anyone with the link → Viewer**.
4. Copy the normal Google Sheets share link.
5. Select **Paste Google Sheet Link** in Career Accelerator.

Normal lesson workflow:

1. Select **Open Google Sheet**.
2. Follow the exact task-specific Google Sheets instructions.
3. Wait for Google Sheets to save.
4. Select **Check My Work**.

Career Accelerator downloads the latest public `.xlsx` export from the linked sheet and runs the existing workbook validator. It stores only the spreadsheet ID and share link; Spreadsheet Academy does not require OAuth credentials, a client JSON file, or Google account tokens.

See [Spreadsheet Academy Google Sheets](docs/SPREADSHEET_ACADEMY_GOOGLE_SHEETS.md).

## Learning and practice

The consolidated Learning workspace includes:

- Accelerator Academy pathways and assessments
- Google Data Analytics Certificate tracking
- Spreadsheet, SQL, Power BI, Python, and pandas learning
- DuckDB exercises and SQL interview practice
- Skills Labs and demonstrated evidence

Retired Exercise Packs are no longer part of the application or repository.

## Repository structure

```text
Career Accelerator.bat          Windows launcher
Launch-Career-Accelerator.ps1   Bootstrap and runtime launcher
application/                    PySide6 application source and configuration
curriculum/                     Academy curriculum, datasets, and workbook template
data/                           Local databases and runtime state
documentation/                  Current product, roadmap, and technical documentation
docs/                           Focused user setup guides
practice/                       DuckDB and applied-practice workspaces
projects/                       Portfolio projects and milestones
resources/                      SQL, career, and learning resources
career/                         Resume, LinkedIn, interview, and application materials
weeks/                          Weekly sprint plans and retrospectives
workspaces/                     Managed task workspaces
backups/                        Current learner database backups
```

Generated caches, retired patch backups, historical installers, and obsolete learning-pack folders do not belong in the active repository.

## Local data and backups

Primary progress is stored in:

```text
data/career_accelerator.db
```

Learner databases, portfolio work, submissions, career files, current database backups, `.git`, and `.venv` are preserved during application updates. **Settings → Reset All Progress** creates an external safety backup before rebuilding the starter state.

## Keyboard shortcuts

- `Ctrl+K` — Command palette
- `Ctrl+S` — Create a local database backup

## Core documents

- [Master Roadmap](documentation/MASTER_ROADMAP.md)
- [Current Progress](documentation/PROGRESS.md)
- [Quick Start](documentation/QUICK_START.md)
- [Contributing Workflow](documentation/CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## Guiding principle

**Learn → Apply → Document → Present**
