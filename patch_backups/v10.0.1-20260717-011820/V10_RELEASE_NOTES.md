# Career Accelerator v10.0.0 Release Notes

Release date: July 16, 2026

Career Accelerator v10.0.0 is a cumulative rebuild on the confirmed v9.6.4 baseline. It restores the changes that were lost during the revert and tightens the Exercise Pack learning flow around real learner practice.

## Exercise Packs

- Every lesson is associated with one or more ordered practice questions.
- Selecting a lesson loads those questions directly in the Practice card.
- New answers contain only the question's intentionally minimal starting template, or an empty editor when the pack disables scaffolding.
- Lesson examples and official solutions are never copied into the editor automatically.
- Saved learner SQL, notes, results, hint level, and completion state remain independent per question.
- Run Query, Check Answer, Exercise Hint, and View Solution operate on the selected question.
- Official solutions remain in a separate walkthrough and do not overwrite learner SQL.

## SQL workspaces

- Exercise Packs, DuckDB Exercises, Applied Labs, and Interview Problems use the same line-numbered SQL editor.
- The editor includes syntax highlighting, a synchronized gutter, current-line emphasis, error-line emphasis, horizontal scrolling, and DuckDB error navigation.
- Interview Problems now support editable in-app submissions, saved notes, completion validation, and submission-file reopening.
- Completing original Interview Problem work creates duplicate-resistant Demonstrated Evidence. Merely viewing a solution does not.

## Dashboard and routing

- Completed Today’s Focus tasks remain visible with a checked, muted, struck-through, non-actionable presentation.
- DuckDB tasks still route to the exact assigned exercise.
- Interview tasks still route to the exact assigned problem.

## Data safety and storage

- Backups use consistent SQLite snapshots, including databases using WAL mode.
- Identical database content does not create duplicate backups.
- Retention keeps the newest 10 backups, daily representatives for seven days, and weekly representatives for four weeks.
- Settings shows database, backup, DuckDB, and combined storage totals.
- Settings includes Clean Old Backups and Open Data Folder controls.

## Content and authoring

- SQL Subqueries and SQL Joins were updated to pack version 2.0.0.
- All bundled lessons now have associated practice questions.
- The standard pack template and authoring documentation enforce the v10 lesson-practice and starter-template rules.

## Upgrade safety

Use the cumulative patch installer when upgrading an existing repository. It validates the target, skips identical files, backs up every file it replaces, and does not delete the local database, backups, submissions, generated DuckDB database, task workspaces, or custom Exercise Packs.
