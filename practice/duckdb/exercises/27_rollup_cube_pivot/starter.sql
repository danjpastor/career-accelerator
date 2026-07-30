-- DuckDB Exercise 19: Build subtotal and pivot-style summaries
-- Read README.md before starting.
-- Save your completed copy under practice/duckdb/submissions/


-- -----------------------------------------------------------------
-- Q1. Task: Create region and product-category subtotals using ROLLUP. Required output: return only these columns in this order: `region`, `product_category`, `revenue`. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q2. Task: Create combinations of region and sales channel using CUBE. Required output: return only these columns in this order: `region`, `sales_channel`, `revenue`. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q3. Task: Build a pivot-style summary with one row per region and separate revenue columns for Online and Store. Required output: return only these columns in this order: `region`, `online_revenue`, `store_revenue`. A correct result contains 4 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q4. Task: Use GROUPING SETS to return region totals, channel totals, and an overall total in one result. Required output: return only these columns in this order: `region`, `sales_channel`, `revenue`. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------

