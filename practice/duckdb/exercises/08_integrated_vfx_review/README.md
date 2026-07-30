# DuckDB Exercise 30: Analyze a VFX production snapshot

**Week:** 7
**Estimated time:** 60 minutes  
**Concepts:** joins, CTEs, CASE, window functions, business interpretation

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

1. Task: Find unfinished shots due before June 30, 2026. Required output: return only these columns in this order: `shot_id`. A correct result contains 5 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
2. Task: Calculate actual logged hours per shot. Required output: return only these columns in this order: `shot_id`, `sum("hours")`. Use these exact names for calculated or summarized columns: `sum("hours")`. A correct result contains 14 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
3. Task: Compare estimated and actual hours for completed shots. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
4. Task: Calculate on-time completion rate by department. Required output: return only these columns in this order: `department`, `round(((100.0 * sum(CASE  WHEN (((status = 'Final') AND (completed_date <= due_date))) THEN (1) ELSE 0 END)) / "nullif"(sum(CASE  WHEN ((status = 'Final')) THEN (1) ELSE 0 END), 0)), 2)`. Use these exact names for calculated or summarized columns: `round(((100.0 * sum(CASE  WHEN (((status = 'Final') AND (completed_date <= due_date))) THEN (1) ELSE 0 END)) / "nullif"(sum(CASE  WHEN ((status = 'Final')) THEN (1) ELSE 0 END), 0)), 2)`. A correct result contains 4 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
5. Task: Create a risk flag using status, due date, revision count, and hours variance. Required output: return only these columns in this order: `sum(CASE  WHEN (((s.status != 'Final') AND ((s.due_date < CAST('2026-06-30' AS "DATE")) OR (s.revision_count >= 3) OR (COALESCE(a.actual_hours, 0) > s.estimated_hours)))) THEN (1) ELSE 0 END)`. Use these exact names for calculated or summarized columns: `sum(CASE  WHEN (((s.status != 'Final') AND ((s.due_date < CAST('2026-06-30' AS "DATE")) OR (s.revision_count >= 3) OR (COALESCE(a.actual_hours, 0) > s.estimated_hours)))) THEN (1) ELSE 0 END)`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
6. Task: Summarize estimated hours, actual hours, and revisions by project. Required output: return only these columns in this order: `project_id`, `sum(estimated_hours)`, `sum(COALESCE(actual_hours, 0))`, `sum(revision_count)`. Use these exact names for calculated or summarized columns: `sum(estimated_hours)`, `sum(COALESCE(actual_hours, 0))`, `sum(revision_count)`. A correct result contains 4 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
7. Task: Rank artists by total logged hours using `DENSE_RANK`. Required output: return only these columns in this order: `artist_id`, `hours`, `workload_rank`. Use these exact names for calculated or summarized columns: `workload_rank`. A correct result contains 7 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
8. Task: Return the highest-risk project and explain the drivers in two sentences. Required output: return only these columns in this order: `project_id`, `risk_shots`. Use these exact names for calculated or summarized columns: `risk_shots`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
## Completion evidence

1. Copy `starter.sql` to:
   `practice/duckdb/submissions/ex08_integrated_vfx_review.sql`
2. Answer every question in that copied file.
3. Run each query successfully in DuckDB.
4. Compare your results with `validation.md` only after attempting the questions.
5. Add a short comment at the bottom explaining one decision or mistake you corrected.

The validation file contains result checkpoints, not completed SQL solutions.
