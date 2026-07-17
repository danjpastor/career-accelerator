# Career Accelerator v10.0.2 Test Results

Verification date: July 17, 2026

## Automated regressions

- `python -m pytest -q`: **24 passed, 76 subtests passed**
- Exercise Pack schema, lesson-question mapping, starter safety, official solutions, and progress migration: passed
- Shared SQL editor line numbering, error navigation, and error reset: passed
- Interview Problem original-work validation: passed
- Backup snapshot deduplication and retention pruning: passed
- Responsive resize cycles, breakpoints, compact card width, guided-workspace height, course-title rebuilding, and page-overflow checks: passed
- Dashboard no-scroll matrix and metric-ring containment: passed
- Sidebar no-scroll matrix and complete-card viewport containment: passed
- Embedded course-extension placement and ghost-pill prevention: passed
- Rounded lesson subtitle height-for-width sizing: passed

## Dashboard visibility matrix

The full PySide6 application was constructed offscreen and the Dashboard was verified at:

- 900×620
- 1024×768
- 1280×800
- 1366×768
- 1536×1020

At every size:

- Dashboard vertical scrollbar maximum: 0
- Dashboard horizontal scrollbar maximum: 0
- Sidebar vertical scrollbar maximum: 0
- All metric, primary, secondary, and footer cards remain in the visible viewport
- Current Streak, Total Study Time, and the sidebar footer remain in the visible viewport
- Every circular progress graphic remains within its card content rectangle
- The intended comfortable, compact, or ultra-compact density mode is applied

## Full application responsive matrix

The application was also resized through 1536×1020, 1280×800, 1024×768, and 900×620. All 12 main pages reported zero outer horizontal-scroll range after repeated wide-to-compact-to-wide cycles:

- Dashboard
- Adaptive Planner
- Learning
- Portfolio Workspace
- SQL Companion
- Study Session
- Job Readiness
- Applications
- Weekly Summary
- Publish & Git
- Task Workspaces
- Settings

Long-form learning and SQL workspaces remain vertically scrollable where their full instructional content exceeds the viewport.

## Targeted visual regressions

- Applied Lab embedded progress panel is reinserted below the lesson header and does not float behind the type pill: passed
- Wrapped rounded subtitles receive at least their calculated height-for-width: passed
- Applied Labs long subtitle pill displays without vertical clipping: passed
- DuckDB Exercises long subtitle pill displays without vertical clipping: passed
- Exercise Pack lesson header remains clean and correctly spaced: passed
- Circular Dashboard progress values and labels remain vertically centered: passed
- Circular Study Session timer remains contained at ultra-compact density: passed

## Package verification

The clean release is compiled and tested again after runtime/private files are removed. The cumulative installer was applied independently to the uploaded v9.6.4 repository and to v10.0.1, with sentinel databases, custom packs, learner SQL, backups, generated DuckDB data, and task workspaces preserved. A second installer run against each target reported zero replacements. Both upgraded copies completed an offscreen 900×620 startup and no-scroll front-page check.
