-- DuckDB Exercise 29: Plan partitioning and access-safe outputs
-- Read README.md before starting.
-- Save your completed copy under practice/duckdb/submissions/


-- -----------------------------------------------------------------
-- Q1. Task: Summarize order volume by month to evaluate a possible date partition key. Required output: return only these columns in this order: `order_month`, `order_count`. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q2. Task: Summarize order volume by region to evaluate whether region would create balanced partitions. Required output: return only these columns in this order: `region`, `order_count`. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q3. Task: Create a restricted customer output that excludes signup date while retaining the analytical key and region. Required output: return only these columns in this order: `customer_id`, `customer_name`, `region`. A correct result contains 10 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q4. Task: Create a restricted order output that exposes order status and total without customer names. Required output: return only these columns in this order: `order_id`, `customer_id`, `order_total`, `order_status`. A correct result contains 14 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------

