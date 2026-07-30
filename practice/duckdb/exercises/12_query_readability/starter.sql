-- DuckDB Exercise 13: Refactor a complex query with readable CTEs
-- Source instructions: README.md
-- Save your completed copy under practice/duckdb/submissions/

-- Confirm the relevant tables exist.
DESCRIBE ex12_campaign_performance;


-- -----------------------------------------------------------------
-- Q1. Task: Run `messy_query.sql` and record its output. Required output: return only these columns in this order: `campaign_channel`, `sum(spend)`, `sum(revenue)`, `(sum(revenue) - sum(spend))`, `round((sum(revenue) / "nullif"(sum(spend), 0)), 4)`. Use these exact names for calculated or summarized columns: `sum(spend)`, `sum(revenue)`, `(sum(revenue) - sum(spend))`, `round((sum(revenue) / "nullif"(sum(spend), 0)), 4)`. A correct result contains 4 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q2. Task: Reformat the query using one clause per line and consistent indentation. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q3. Task: Replace positional `ORDER BY 5` with a descriptive alias. Required output: return only these columns in this order: `count(DISTINCT campaign_channel)`. Use these exact names for calculated or summarized columns: `count(DISTINCT campaign_channel)`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q4. Task: Move channel aggregation into a clearly named CTE. Required output: return only these columns in this order: `round(sum(spend), 2)`, `round(sum(revenue), 2)`. Use these exact names for calculated or summarized columns: `round(sum(spend), 2)`, `round(sum(revenue), 2)`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q5. Task: Add short comments explaining the CTE and final filter. Required output: return only these columns in this order: `campaign_channel`, `profit`. Use these exact names for calculated or summarized columns: `profit`. A correct result contains 4 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q6. Task: Confirm the refactored result exactly matches the original. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q7. Task: Write two sentences explaining how readability reduces analytics risk. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------
