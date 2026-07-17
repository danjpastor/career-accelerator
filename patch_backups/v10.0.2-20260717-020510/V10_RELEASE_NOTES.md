# Career Accelerator v10.0.1 Release Notes

Release date: July 17, 2026

Career Accelerator v10.0.1 is the polished cumulative v10 release. It keeps the lesson-driven Exercise Pack, shared SQL editor, Interview Evidence, routing, and backup improvements from v10.0.0 while rebuilding the application shell and every major page for reliable window resizing.

## Responsive layout polish

- The supported minimum window is now 900×620.
- Every main page uses a scroll-safe responsive shell with adaptive margins and header placement.
- Dashboard content switches between true wide, medium, and compact layouts instead of remaining forced into the wide grid.
- Compact Dashboard mode uses readable full-width cards rather than squeezing narrow secondary columns.
- Reusable cards, task rows, focus rows, badge cards, labels, and long list entries wrap and grow vertically instead of forcing hidden overflow.
- Application typography and inline Qt styles scale with the available window dimensions.
- Sidebar width, navigation controls, progress rings, and circular timers scale with the shell.
- Grid reflow clears obsolete row and column stretch values, preventing one-column cards from remaining trapped at half width after a resize.
- Learning, Portfolio, SQL Companion, Study Session, Job Readiness, Applications, Weekly Summary, Publish & Git, Task Workspaces, and Settings all have page-specific breakpoints.
- The unified Task Workspace dialog sizes itself relative to the parent window and reflows its action rows on narrower displays.

## Guided learning workspaces

- Exercise Packs and DuckDB Exercises become deliberately tall, outer-scrollable workspaces at compact widths.
- Navigation, Learn, and Practice receive usable minimum heights instead of being divided into very short nested splitter panes.
- Lesson columns, course headers, action groups, result areas, editors, and navigation footers continue to reflow internally.
- Rapid lesson rebuilding no longer leaves a temporarily duplicated or overlapping course title.

## v10 learning and evidence features retained

- Every Exercise Pack lesson is associated with one or more ordered practice questions.
- New answers contain only minimal authored scaffolding; examples and solutions are not inserted automatically.
- Run Query, Check Answer, progressive Exercise Hint, and separate View Solution workflows remain functional.
- Exercise Packs, DuckDB Exercises, Applied Labs, and Interview Problems share the numbered SQL editor with syntax highlighting and DuckDB error navigation.
- Interview Problem submissions create duplicate-resistant Demonstrated Evidence only from original learner work.
- Exact DuckDB and Interview Problem routing is preserved.
- Completed Today’s Focus rows remain visible, styled as complete, and non-actionable.
- SQLite backup deduplication, retention pruning, storage reporting, and Settings cleanup controls remain active.

## Upgrade safety

Use the cumulative patch installer to upgrade either v9.6.4 or v10.0.0. It validates the target repository, skips identical files, backs up each replaced file under `patch_backups/v10.0.1-<timestamp>/`, and preserves local databases, backups, submissions, task workspaces, generated datasets, and custom Exercise Packs.
