-- DuckDB Exercise 03: Clean customer feedback
-- Source instructions: README.md
-- Save your completed copy under practice/duckdb/submissions/

-- Confirm the relevant tables exist.
DESCRIBE ex03_customer_feedback_dirty;


-- -----------------------------------------------------------------
-- Q1. Inspect distinct raw values for `channel_raw` and `resolved_raw`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q2. Create a normalized channel using `UPPER(TRIM(channel_raw))`; convert blanks to NULL.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q3. Create `rating_clean` with `TRY_CAST`; keep only ratings from 1 through 5.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q4. Create `response_minutes_clean`; convert invalid or negative values to NULL.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q5. Create a numeric `resolved_flag` where common true values equal 1, false values equal 0, and unknown values remain NULL.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q6. Create an `issue_type_clean` value in title case or a fallback of `Unknown`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q7. Create a view named `ex03_feedback_clean` containing the cleaned fields and a `quality_issue_flag`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------
