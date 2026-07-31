# DuckDB Exercise 23: Clean and standardize customer feedback

**Week:** 6
**Estimated time:** 45 minutes  
**Concepts:** NULLIF, TRIM, COALESCE, TRY_CAST, CASE

## Scenario

A customer-experience export contains blanks, inconsistent labels, invalid numbers, and unreliable boolean values.

## Tables

- `ex03_customer_feedback_dirty`

## Source CSV files

- `customer_feedback_dirty.csv`

## Tasks

### Task 1

Inspect distinct raw values for `channel_raw` and `resolved_raw`.

**Result requirements**

- **Return columns:** `count(DISTINCT main."trim"(channel_raw))`, `count(DISTINCT main."trim"(resolved_raw))`
- **Exact names for new columns:** `count(DISTINCT main."trim"(channel_raw))`, `count(DISTINCT main."trim"(resolved_raw))`
- **Expected rows:** 1

### Task 2

Create a normalized channel using `UPPER(TRIM(channel_raw))`; convert blanks to NULL.

**Result requirements**

- **Return columns:** `count_star()`
- **Exact names for new columns:** `count_star()`
- **Expected rows:** 1

### Task 3

Create `rating_raw` with `TRY_CAST`; keep only ratings from 1 through 5.

**Result requirements**

- **Return columns:** `count_star()`
- **Exact names for new columns:** `count_star()`
- **Expected rows:** 1

### Task 4

Create `response_minutes_raw`; convert invalid or negative values to NULL.

**Result requirements**

- **Return columns:** `count_star()`
- **Exact names for new columns:** `count_star()`
- **Expected rows:** 1

### Task 5

Create a numeric `resolved_raw` where common true values equal 1, false values equal 0, and unknown values remain NULL.

**Result requirements**

- **Return columns:** `sum(CASE  WHEN ((lower(main."trim"(resolved_raw)) IN ('yes', 'y', '1', 'true'))) THEN (1) ELSE 0 END)`, `sum(CASE  WHEN ((lower(main."trim"(resolved_raw)) IN ('no', 'n', '0', 'false'))) THEN (1) ELSE 0 END)`
- **Exact names for new columns:** `sum(CASE  WHEN ((lower(main."trim"(resolved_raw)) IN ('yes', 'y', '1', 'true'))) THEN (1) ELSE 0 END)`, `sum(CASE  WHEN ((lower(main."trim"(resolved_raw)) IN ('no', 'n', '0', 'false'))) THEN (1) ELSE 0 END)`
- **Expected rows:** 1

### Task 6

Create an `issue_type_raw` value in title case or a fallback of `Unknown`.

**Result requirements**

- **Return columns:** `count_star()`
- **Exact names for new columns:** `count_star()`
- **Expected rows:** 1

### Task 7

Create a view named `ex03_feedback_clean` containing the cleaned fields and a `quality_issue_flag`.

**Result requirements**

- **Return columns:** `count_star()`
- **Exact names for new columns:** `count_star()`
- **Expected rows:** 1
## Completion evidence

1. Copy `starter.sql` to:
   `practice/duckdb/submissions/ex03_nulls_case_cleaning.sql`
2. Answer every question in that copied file.
3. Run each query successfully in DuckDB.
4. Compare your results with `validation.md` only after attempting the questions.
5. Add a short comment at the bottom explaining one decision or mistake you corrected.

The validation file contains result checkpoints, not completed SQL solutions.
