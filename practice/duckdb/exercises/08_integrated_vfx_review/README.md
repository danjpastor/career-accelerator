# DuckDB Exercise 30: Analyze a VFX production snapshot

**Week:** 6
**Estimated time:** 60 minutes  
**Concepts:** joins, CTEs, CASE, window functions, business interpretation

## Scenario

A VFX production manager needs a June 30, 2026 risk review covering deadlines, logged hours, revisions, workload, and artist capacity.

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

- Return columns in this order: `shot_id`.
- Return 5 rows.

### Task 2

Show actual logged hours for each shot. Return `shot_id` and total hours as `actual_hours`.

**Result requirements**

- Return columns in this order: `shot_id`, `actual_hours`.
- Return 14 rows.

### Task 3

Count completed shots whose actual logged hours exceeded their estimate. Return the result as `over_estimate_shots`.

**Result requirements**

- Return columns in this order: `over_estimate_shots`.
- Return 1 row.

### Task 4

Calculate the on-time completion percentage for each department. Round to two decimal places and name it `on_time_completion_pct`.

**Result requirements**

- Return columns in this order: `department`, `on_time_completion_pct`.
- Return 4 rows.
- Round the requested result to 2 decimal places.

### Task 5

Count unfinished shots that are overdue, have at least three revisions, or have logged more hours than estimated. Return the count as `risk_shots`.

**Result requirements**

- Return columns in this order: `risk_shots`.
- Return 1 row.

### Task 6

Summarize workload by project. Return `project_id`, total `estimated_hours`, total `actual_hours`, and total `revisions`.

**Result requirements**

- Return columns in this order: `project_id`, `estimated_hours`, `actual_hours`, `revisions`.
- Return 4 rows.

### Task 7

Rank artists by total logged hours using `DENSE_RANK`.

**Result requirements**

- Return columns in this order: `artist_id`, `hours`, `workload_rank`.
- Return 7 rows.

### Task 8

Return the highest-risk project and explain the drivers in two sentences.

**Result requirements**

- Return columns in this order: `project_id`, `risk_shots`.
- Return 1 row.

## Complete the exercise

1. Complete each task in the SQL editor.
2. Use **Check Task** for specific feedback and hints.
3. Use **Check Exercise** after every task passes.
4. Select **Submit Exercise** to record completion.

