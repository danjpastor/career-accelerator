-- DuckDB Exercise 28: Create reusable views and analytical snapshots
-- Read README.md before starting.
-- Save your completed copy under practice/duckdb/submissions/


-- -----------------------------------------------------------------
-- Q1. Task: Create a reusable view that joins delivered orders to customer region, then return the view rows. Required output: return only these columns in this order: `order_id`, `customer_id`, `region`, `order_total`. A correct result contains 12 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q2. Task: Query the reusable view to summarize delivered revenue by region. Required output: return only these columns in this order: `region`, `delivered_revenue`. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q3. Task: Create a physical snapshot table from the view and return its row count. Required output: return only these columns in this order: `snapshot_rows`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q4. Task: Compare the view and snapshot row counts to verify the snapshot was created correctly. Required output: return only these columns in this order: `view_rows`, `snapshot_rows`, `difference`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------

