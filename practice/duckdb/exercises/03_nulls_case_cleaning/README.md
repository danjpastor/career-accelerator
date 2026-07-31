# DuckDB Exercise 23: Clean customer feedback

**Week:** 5
**Estimated time:** 45 minutes  
**Concepts:** NULLIF, TRIM, COALESCE, TRY_CAST, CASE

## Scenario

A customer-experience export contains blanks, inconsistent labels, invalid numbers, and unreliable yes-or-no values. The analytics team must clean it before reporting.

## Tables

- `ex03_customer_feedback_dirty`

## Source CSV files

- `customer_feedback_dirty.csv`

## Tasks

### Task 1

Before cleaning the feedback file, count the distinct trimmed labels in `channel_raw` and `resolved_raw`. Name the results `distinct_channel_labels` and `distinct_resolved_labels`.

**Result requirements**

- Return columns in this order: `distinct_channel_labels`, `distinct_resolved_labels`.
- Return 1 row.

### Task 2

Standardize `channel_raw` with `UPPER(TRIM(...))`, turn blank values into NULL, and count the rows that remain blank. Name the result `blank_channel_rows`.

**Result requirements**

- Return columns in this order: `blank_channel_rows`.
- Return 1 row.

### Task 3

Convert `rating_raw` to a number safely, keep values from 1 through 5, and count the valid ratings. Name the result `valid_rating_rows`.

**Result requirements**

- Return columns in this order: `valid_rating_rows`.
- Return 1 row.

### Task 4

Convert `response_minutes_raw` to a number safely, treat invalid or negative values as NULL, and count the valid nonnegative response times. Name the result `valid_response_time_rows`.

**Result requirements**

- Return columns in this order: `valid_response_time_rows`.
- Return 1 row.

### Task 5

Standardize common true and false values in `resolved_raw`. Return the true count as `resolved_yes_rows` and the false count as `resolved_no_rows`; leave unknown values out of both counts.

**Result requirements**

- Return columns in this order: `resolved_yes_rows`, `resolved_no_rows`.
- Return 1 row.

### Task 6

Standardize `issue_type_raw` to title case, replace missing values with `Unknown`, and count the rows labeled `Unknown`. Name the result `unknown_issue_rows`.

**Result requirements**

- Return columns in this order: `unknown_issue_rows`.
- Return 1 row.

### Task 7

Build the cleaned feedback result and count the rows where `quality_issue_flag` identifies a problem. Name the result `quality_issue_rows`.

**Result requirements**

- Return columns in this order: `quality_issue_rows`.
- Return 1 row.

## Complete the exercise

1. Complete each task in the SQL editor.
2. Use **Check Task** for specific feedback and hints.
3. Use **Check Exercise** after every task passes.
4. Select **Submit Exercise** to record completion.

