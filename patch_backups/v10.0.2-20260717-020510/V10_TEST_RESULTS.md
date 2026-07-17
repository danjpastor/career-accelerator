# Career Accelerator v10.0.1 Test Results

Verification date: July 17, 2026

## Automated regressions

- `python -m pytest -q`: **20 passed, 66 subtests passed**
- Exercise Pack schema, lesson-question mapping, starter safety, official solutions, and progress migration: passed
- Shared SQL editor line numbering, error navigation, and error reset: passed
- Interview Problem original-work validation: passed
- Backup snapshot deduplication and retention pruning: passed
- Responsive resize cycles, breakpoints, compact card width, guided-workspace height, course-title rebuilding, and page overflow checks: passed

## Responsive application matrix

The full PySide6 application was constructed offscreen and resized through:

- 1536×1020
- 1280×800
- 1024×768
- 900×620

At both 1536×1020 and 900×620, all 12 main pages reported zero outer horizontal-scroll range:

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

Additional checks:

- Dashboard switches among wide, medium, and compact layouts: passed
- Compact Settings and Study cards occupy the full available page width: passed
- Exercise Packs use vertical compact splitters and at least 1400 pixels of scrollable workspace height: passed
- DuckDB Exercises use vertical compact splitters and at least 1400 pixels of scrollable workspace height: passed
- Compact lesson workspaces remain reachable through the outer page scrollbar: passed
- Rapid course-page rebuilding leaves one visible title and no stale overlapping title: passed
- Unified Task Workspace fits inside a 900×620 parent and reflows action rows: passed

## Visual smoke review

Screenshots were reviewed at the supported minimum and the reference desktop size. Cards remain inside the viewport, long text wraps, narrow pages use vertical reflow, and wide layouts retain the intended multi-column presentation.

## Package verification

The final release package is compiled and tested again after private/generated runtime data is removed. The cumulative installer is also applied to a fresh v10.0.0 copy twice to verify data preservation and idempotence.
