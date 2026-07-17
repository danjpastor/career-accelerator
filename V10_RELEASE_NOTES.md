# Career Accelerator v10.0.4 Release Notes

## Dashboard fit correction

Career Accelerator v10.0.4 removes the remaining Dashboard scrolling regression. The front page now calculates all four card-row heights from the live client viewport, so the complete Dashboard remains visible without a vertical scrollbar at supported desktop sizes and at common Windows display-scaling dimensions.

The Study Session card now reserves a dedicated timer region using the circular timer's actual scaled size. The timer can no longer extend behind the Start, Pause, Reset, or Log controls when compact density is active.

## Header date correction

Dates on Adaptive Planner, Learning, Portfolio Workspace, SQL Companion, Study Session, Job Readiness, Applications, Weekly Summary, Publish & Git, Settings, and Task Workspaces remain on one line. On narrow layouts the intact date moves below the page title instead of wrapping into multiple lines.

## Upgrade safety

The cumulative v10.0.4 installer may be applied to v9.6.4 or any v10 release. It backs up replaced files, skips identical files on repeated runs, and preserves databases, progress, learner submissions, backups, generated DuckDB data, task workspaces, and custom Exercise Packs.
