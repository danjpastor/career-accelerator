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

## Tasks

### Task 1

Find unfinished shots due before June 30, 2026.

**Result requirements**

- **Return columns:** `shot_id`
- **Expected rows:** 5

### Task 2

Calculate actual logged hours per shot.

**Result requirements**

- **Return columns:** `shot_id`, `sum("hours")`
- **Exact names for new columns:** `sum("hours")`
- **Expected rows:** 14

### Task 3

Compare estimated and actual hours for completed shots.

**Result requirements**

- **Return columns:** `count_star()`
- **Exact names for new columns:** `count_star()`
- **Expected rows:** 1

### Task 4

Calculate on-time completion rate by department.

**Result requirements**

- **Return columns:** `department`, `round(((100.0 * sum(CASE  WHEN (((status = 'Final') AND (completed_date <= due_date))) THEN (1) ELSE 0 END)) / "nullif"(sum(CASE  WHEN ((status = 'Final')) THEN (1) ELSE 0 END), 0)), 2)`
- **Exact names for new columns:** `round(((100.0 * sum(CASE  WHEN (((status = 'Final') AND (completed_date <= due_date))) THEN (1) ELSE 0 END)) / "nullif"(sum(CASE  WHEN ((status = 'Final')) THEN (1) ELSE 0 END), 0)), 2)`
- **Expected rows:** 4

### Task 5

Create a risk flag using status, due date, revision count, and hours variance.

**Result requirements**

- **Return columns:** `sum(CASE  WHEN (((s.status != 'Final') AND ((s.due_date < CAST('2026-06-30' AS "DATE")) OR (s.revision_count >= 3) OR (COALESCE(a.actual_hours, 0) > s.estimated_hours)))) THEN (1) ELSE 0 END)`
- **Exact names for new columns:** `sum(CASE  WHEN (((s.status != 'Final') AND ((s.due_date < CAST('2026-06-30' AS "DATE")) OR (s.revision_count >= 3) OR (COALESCE(a.actual_hours, 0) > s.estimated_hours)))) THEN (1) ELSE 0 END)`
- **Expected rows:** 1

### Task 6

Summarize estimated hours, actual hours, and revisions by project.

**Result requirements**

- **Return columns:** `project_id`, `sum(estimated_hours)`, `sum(COALESCE(actual_hours, 0))`, `sum(revision_count)`
- **Exact names for new columns:** `sum(estimated_hours)`, `sum(COALESCE(actual_hours, 0))`, `sum(revision_count)`
- **Expected rows:** 4

### Task 7

Rank artists by total logged hours using `DENSE_RANK`.

**Result requirements**

- **Return columns:** `artist_id`, `hours`, `workload_rank`
- **Exact names for new columns:** `workload_rank`
- **Expected rows:** 7

### Task 8

Return the highest-risk project and explain the drivers in two sentences.

**Result requirements**

- **Return columns:** `project_id`, `risk_shots`
- **Exact names for new columns:** `risk_shots`
- **Expected rows:** 1
## Completion evidence

1. Copy `starter.sql` to:
   `practice/duckdb/submissions/ex08_integrated_vfx_review.sql`
2. Answer every question in that copied file.
3. Run each query successfully in DuckDB.
4. Compare your results with `validation.md` only after attempting the questions.
5. Add a short comment at the bottom explaining one decision or mistake you corrected.

The validation file contains result checkpoints, not completed SQL solutions.
