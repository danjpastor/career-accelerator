# Career Accelerator v10.0.5 Release Notes

## Dashboard action-button correction

Dashboard action controls now size themselves against the active scaled font and stylesheet metrics. Responsive density can still reduce card height, but it can no longer force Start Study Session, Pause, Reset, Log, View Full Summary, Continue Highest-Impact Task, or View Job Readiness below the height required to render their labels cleanly. Dashboard-specific padding keeps the controls compact enough for the no-scroll front page.

## Flexible sidebar navigation

The navigation links now occupy a dedicated flexible region between the Career Accelerator logo and the Current Streak card. Each link receives an equal share of the available height, eliminating the large empty band that previously appeared on taller or display-scaled windows while preserving the no-scroll 900×620 minimum layout.

## Rebuild today’s snapshot

Settings → Data and Recovery now includes **Rebuild Today’s Snapshot**. The action discards only the current calendar day’s frozen Today’s Focus recommendation and regenerates it from live progress, track state, prerequisites, and roadmap priorities. It does not erase task completions, notes, study sessions, achievements, historical daily snapshots, or other progress. If regeneration fails, the original current-day snapshot is restored automatically.

## Upgrade safety

The cumulative v10.0.5 installer may be applied to v9.6.4 or any v10 release. It backs up replaced files, skips identical files on repeated runs, and preserves databases, progress, learner submissions, backups, generated DuckDB data, task workspaces, and custom Exercise Packs.
