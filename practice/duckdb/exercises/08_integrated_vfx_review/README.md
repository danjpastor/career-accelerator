# DuckDB Exercise 08: Analyze a VFX production snapshot

**Week:** 9  
**Estimated time:** 60 minutes  
**Concepts:** filtering, joins, aggregation, CASE, CTEs, ranking

## Scenario

A VFX production manager needs a compact risk review as of June 30, 2026.

## Tables

- `ex08_projects`
- `ex08_shots`
- `ex08_time_entries`

## Source CSV files

- `projects.csv`
- `shots.csv`
- `time_entries.csv`

## Questions

1. Find unfinished shots due before June 30, 2026.
2. Calculate actual logged hours per shot.
3. Compare estimated and actual hours for completed shots.
4. Calculate on-time completion rate by department.
5. Create a risk flag using status, due date, revision count, and hours variance.
6. Summarize estimated hours, actual hours, and revisions by project.
7. Rank artists by total logged hours using `DENSE_RANK`.
8. Return the highest-risk project and explain the drivers in two sentences.

## Completion evidence

1. Copy `starter.sql` to:
   `practice/duckdb/submissions/ex08_integrated_vfx_review.sql`
2. Answer every question in that copied file.
3. Run each query successfully in DuckDB.
4. Compare your results with `validation.md` only after attempting the questions.
5. Add a short comment at the bottom explaining one decision or mistake you corrected.

The validation file contains result checkpoints, not completed SQL solutions.
