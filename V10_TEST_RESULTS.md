# Career Accelerator v10.0.0 Test Results

Test date: July 16, 2026

## Automated regression suite

- Python compilation for `app.py` and all `career_app` modules: passed
- Focused `unittest` suite: **15 tests passed**
- Exercise Pack manifest and association validation: passed
- Every lesson has associated, uniquely ordered questions: passed
- Manifest and question JSON associations agree: passed
- Minimal starter-template safety: passed
- All official SQL Subqueries solutions: passed
- All official SQL Joins solutions: passed
- Standard authoring-template solution: passed
- Existing progress-table migration for saved hint levels: passed
- Per-question hint-level persistence: passed
- Shared SQL editor line numbers and DuckDB error navigation: passed
- Editing clears stale error highlighting: passed
- Completed Today’s Focus actions are disabled: passed
- Interview starting-template completion guard: passed
- SQLite backup content deduplication: passed
- Backup newest/daily/weekly retention: passed

## Clean packaged-copy smoke test

The application was launched from a clean staging copy with `QT_QPA_PLATFORM=offscreen` and no preexisting user database.

- Full `CareerAccelerator` window construction: passed
- Window and internal version report `10.0.0`: passed
- Bundled/installed pack discovery: 2 packs loaded
- Shared `SqlCodeEditor` present in Exercise Packs, DuckDB Exercises, Applied Labs, and Interview Problems: passed
- Selecting a lesson with multiple questions populates the Practice selector: passed
- A brand-new question opens with only its minimal starting template: passed
- Progressive hints reveal one step at a time and survive question switching: passed
- An official solution passes Check Answer without changing submitted SQL: passed
- Viewing the solution and closing it without Copy to Editor preserves learner SQL: passed
- Exact DuckDB routing selected Exercise 06: passed
- Exact Interview Problem routing selected Histogram of Tweets: passed
- Saving an Interview submission before completion created no evidence: passed
- Completing the Interview submission twice produced exactly one evidence record: passed
- Settings storage summary constructed successfully: passed

## Release cleanliness

The clean build excludes Git history, virtual environments, Python caches, the local SQLite database, backup history, patch backups, the generated DuckDB database, learner DuckDB submissions, learner DataLemur solutions, task workspace files, and the generated Windows shortcut.

## Installer verification

The cumulative patch was applied to a fresh extraction of the uploaded v9.6.4 package.

- Existing repository validation: passed
- First application replaced 63 files and added 7 missing v10 files: passed
- Every replaced file was backed up under `patch_backups/v10.0.0-<timestamp>/`: passed
- Existing `data/career_accelerator.db` SHA-256 remained unchanged: passed
- A custom installed-pack file remained present: passed
- Second application reported 0 replaced and 0 added files: passed
- Second application created no unnecessary backup folder: passed
- Patched repository compilation: passed
- Patched repository offscreen application startup as v10.0.0: passed
