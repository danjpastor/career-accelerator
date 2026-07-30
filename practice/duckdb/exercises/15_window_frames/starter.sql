-- DuckDB Exercise 17: Calculate running totals and moving averages
-- Source instructions: README.md
-- Save your completed work through Career Accelerator.

DESCRIBE ex15_daily_revenue;

-- -----------------------------------------------------------------
-- Q1. Task: Number each region’s rows in date order. Required output: return only these columns in this order: `region`, `revenue_date`, `row_number`. Use these exact names for calculated or summarized columns: `row_number`. A correct result contains 14 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q2. Task: Calculate cumulative revenue by region. Required output: return only these columns in this order: `region`, `final_running_total`. Use these exact names for calculated or summarized columns: `final_running_total`. A correct result contains 2 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q3. Task: Calculate a trailing three-day moving average by region. Required output: return only these columns in this order: `region`, `moving_avg_on_2026_06_07`. Use these exact names for calculated or summarized columns: `moving_avg_on_2026_06_07`. A correct result contains 2 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q4. Task: Use LAG to calculate the day-over-day revenue change. Required output: return only these columns in this order: `region`, `change_on_2026_06_07`. Use these exact names for calculated or summarized columns: `change_on_2026_06_07`. A correct result contains 2 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q5. Task: Rank each day within its region from highest to lowest revenue. Required output: return only these columns in this order: `region`, `highest_revenue_date`. Use these exact names for calculated or summarized columns: `highest_revenue_date`. A correct result contains 2 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q6. Task: Return only the top two revenue days per region. Required output: return only these columns in this order: `region`, `revenue_date`, `revenue`. A correct result contains 4 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q7. Task: Explain in a SQL comment how ROWS BETWEEN changes the moving-average frame. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


