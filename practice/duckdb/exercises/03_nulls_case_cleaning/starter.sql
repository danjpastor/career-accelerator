-- DuckDB Exercise 23: Clean customer feedback
-- Source instructions: README.md
-- Save your completed copy under practice/duckdb/submissions/

-- Confirm the relevant tables exist.
DESCRIBE ex03_customer_feedback_dirty;


-- -----------------------------------------------------------------
-- Q1. Before cleaning the feedback file, count the distinct trimmed labels in `channel_raw` and `resolved_raw`. Name the results `distinct_channel_labels` and `distinct_resolved_labels`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q2. Standardize `channel_raw` with `UPPER(TRIM(...))`, turn blank values into NULL, and count the rows that remain blank. Name the result `blank_channel_rows`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q3. Convert `rating_raw` to a number safely, keep values from 1 through 5, and count the valid ratings. Name the result `valid_rating_rows`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q4. Convert `response_minutes_raw` to a number safely, treat invalid or negative values as NULL, and count the valid nonnegative response times. Name the result `valid_response_time_rows`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q5. Standardize common true and false values in `resolved_raw`. Return the true count as `resolved_yes_rows` and the false count as `resolved_no_rows`; leave unknown values out of both counts.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q6. Standardize `issue_type_raw` to title case, replace missing values with `Unknown`, and count the rows labeled `Unknown`. Name the result `unknown_issue_rows`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q7. Build the cleaned feedback result and count the rows where `quality_issue_flag` identifies a problem. Name the result `quality_issue_rows`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------
