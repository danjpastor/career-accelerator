-- DuckDB Exercise 22: Calculate subscription KPIs
-- Source instructions: README.md
-- Save your completed copy under practice/duckdb/submissions/

-- Confirm the relevant tables exist.
DESCRIBE ex04_subscriptions;


-- -----------------------------------------------------------------
-- Q1. Task: Calculate active monthly recurring revenue (MRR). Required output: return only these columns in this order: `sum(monthly_revenue)`. Use these exact names for calculated or summarized columns: `sum(monthly_revenue)`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q2. Task: Count active subscriptions. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q3. Task: Calculate average revenue per active subscription. Required output: return only these columns in this order: `round(avg(monthly_revenue), 2)`. Use these exact names for calculated or summarized columns: `round(avg(monthly_revenue), 2)`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q4. Task: Calculate active MRR by plan. Required output: return only these columns in this order: `plan`, `sum(monthly_revenue)`. Use these exact names for calculated or summarized columns: `sum(monthly_revenue)`. A correct result contains 3 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q5. Task: Count June 2026 cancellations. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q6. Task: Calculate June logo churn: June cancellations divided by subscriptions active at the start of June. Required output: return only these columns in this order: `round(((100.0 * canceled) / opening), 2)`. Use these exact names for calculated or summarized columns: `round(((100.0 * canceled) / opening), 2)`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q7. Task: Return each region's share of active MRR as a percentage. Required output: return only these columns in this order: `region`, `round(((100.0 * mrr) / sum(mrr) OVER ()), 2)`. Use these exact names for calculated or summarized columns: `round(((100.0 * mrr) / sum(mrr) OVER ()), 2)`. A correct result contains 4 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------
