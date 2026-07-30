-- DuckDB Exercise 23: Clean and standardize customer feedback
-- Source instructions: README.md
-- Save your completed copy under practice/duckdb/submissions/

-- Confirm the relevant tables exist.
DESCRIBE ex03_customer_feedback_dirty;


-- -----------------------------------------------------------------
-- Q1. Task: Inspect distinct raw values for `channel_raw` and `resolved_raw`. Required output: return only these columns in this order: `count(DISTINCT main."trim"(channel_raw))`, `count(DISTINCT main."trim"(resolved_raw))`. Use these exact names for calculated or summarized columns: `count(DISTINCT main."trim"(channel_raw))`, `count(DISTINCT main."trim"(resolved_raw))`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q2. Task: Create a normalized channel using `UPPER(TRIM(channel_raw))`; convert blanks to NULL. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q3. Task: Create `rating_raw` with `TRY_CAST`; keep only ratings from 1 through 5. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q4. Task: Create `response_minutes_raw`; convert invalid or negative values to NULL. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q5. Task: Create a numeric `resolved_raw` where common true values equal 1, false values equal 0, and unknown values remain NULL. Required output: return only these columns in this order: `sum(CASE  WHEN ((lower(main."trim"(resolved_raw)) IN ('yes', 'y', '1', 'true'))) THEN (1) ELSE 0 END)`, `sum(CASE  WHEN ((lower(main."trim"(resolved_raw)) IN ('no', 'n', '0', 'false'))) THEN (1) ELSE 0 END)`. Use these exact names for calculated or summarized columns: `sum(CASE  WHEN ((lower(main."trim"(resolved_raw)) IN ('yes', 'y', '1', 'true'))) THEN (1) ELSE 0 END)`, `sum(CASE  WHEN ((lower(main."trim"(resolved_raw)) IN ('no', 'n', '0', 'false'))) THEN (1) ELSE 0 END)`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q6. Task: Create an `issue_type_raw` value in title case or a fallback of `Unknown`. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q7. Task: Create a view named `ex03_feedback_clean` containing the cleaned fields and a `quality_issue_flag`. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------
