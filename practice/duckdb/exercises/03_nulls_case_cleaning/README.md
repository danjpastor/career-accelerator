# DuckDB Exercise 03: Clean customer feedback

**Week:** 4  
**Estimated time:** 45 minutes  
**Concepts:** NULLIF, TRIM, COALESCE, TRY_CAST, CASE

## Scenario

A customer-experience export contains blanks, inconsistent labels, invalid numbers, and unreliable boolean values.

## Tables

- `ex03_customer_feedback_dirty`

## Source CSV files

- `customer_feedback_dirty.csv`

## Questions

1. Inspect distinct raw values for `channel_raw` and `resolved_raw`.
2. Create a normalized channel using `UPPER(TRIM(channel_raw))`; convert blanks to NULL.
3. Create `rating_clean` with `TRY_CAST`; keep only ratings from 1 through 5.
4. Create `response_minutes_clean`; convert invalid or negative values to NULL.
5. Create a numeric `resolved_flag` where common true values equal 1, false values equal 0, and unknown values remain NULL.
6. Create an `issue_type_clean` value in title case or a fallback of `Unknown`.
7. Create a view named `ex03_feedback_clean` containing the cleaned fields and a `quality_issue_flag`.

## Completion evidence

1. Copy `starter.sql` to:
   `practice/duckdb/submissions/ex03_nulls_case_cleaning.sql`
2. Answer every question in that copied file.
3. Run each query successfully in DuckDB.
4. Compare your results with `validation.md` only after attempting the questions.
5. Add a short comment at the bottom explaining one decision or mistake you corrected.

The validation file contains result checkpoints, not completed SQL solutions.
