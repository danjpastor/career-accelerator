# Career Accelerator v10.0.2 Release Notes

Release date: July 17, 2026

Career Accelerator v10.0.2 completes the responsive polish pass with targeted corrections to the Dashboard and shared learning renderer. It keeps the cumulative v10 learning, evidence, routing, backup, and storage features while making the front page fully visible without scrolling across the supported desktop-size range.

## No-scroll Dashboard

- Every Dashboard card remains visible without vertical or horizontal scrolling from 900×620 through 1536×1020.
- The complete sidebar also fits without scrolling, including navigation, Current Streak, Total Study Time, and the motivational footer.
- The Dashboard chooses wide or fit card arrangements based on usable viewport width rather than the outer window alone.
- Comfortable, compact, and ultra-compact density modes respond to available height.
- Card heights, internal margins, section spacing, text sizes, progress graphics, task rows, focus rows, badges, summaries, footer metrics, navigation buttons, and sidebar cards scale together.
- Lower-priority explanatory lines collapse only at the densest sizes, while all Dashboard cards and primary values remain visible.
- Repeated wide-to-small-to-wide resizing retains the intended geometry without stale grid spacing or new scroll ranges.

## Circular progress and timer cards

- Circular progress values, labels, captions, and secondary text are now positioned from the live widget rectangle instead of fixed Y coordinates.
- Ring and timer dimensions scale with the current Dashboard density.
- Text is centered and elided safely when space is unusually narrow.
- Progress-ring content stays inside its card at every verified window size.

## Learning header corrections

- Removed the temporary duplicate/ghost pill that could appear behind the main Applied Lab or exercise type label.
- Embedded progress/evidence panels are hidden while a lesson page rebuilds, then reparented and shown only after their proper layout position is restored.
- Rounded lesson subtitles and section subheaders now request their full height-for-width value.
- Long Applied Lab, Exercise Pack, and DuckDB Exercise subtitle pills wrap cleanly instead of clipping their top or bottom edges.

## Cumulative v10 features retained

- Every Exercise Pack lesson has associated practice questions.
- New SQL answers contain only minimal authored starting templates.
- Run Query, Check Answer, progressive Exercise Hint, and separate View Solution remain functional.
- Exercise Packs, DuckDB Exercises, Applied Labs, and Interview Problems share the numbered SQL editor.
- Exact DuckDB and Interview Problem routing remains active.
- Interview Problem submissions create duplicate-resistant Demonstrated Evidence from original learner work.
- Completed Today’s Focus rows remain visible and non-actionable.
- Backup deduplication, retention pruning, storage reporting, and Settings cleanup controls remain active.

## Upgrade safety

The cumulative v10.0.2 patch can be applied to v9.6.4, v10.0.0, or v10.0.1. It validates the target repository, skips identical files, backs up each replaced file under `patch_backups/v10.0.2-<timestamp>/`, and preserves local databases, backups, learner submissions, task workspaces, generated data, and custom Exercise Packs.
