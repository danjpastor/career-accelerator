-- DuckDB Exercise 27: Reshape operational data into analytical tables
-- Read README.md before starting.
-- Save your completed copy under practice/duckdb/submissions/


-- -----------------------------------------------------------------
-- Q1. Task: Return a customer dimension-style result with one row per customer. Required output: return only these columns in this order: `customer_id`, `customer_name`, `region`, `signup_date`. A correct result contains 10 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q2. Task: Return an order fact-style result with order measures and customer key. Required output: return only these columns in this order: `order_id`, `customer_id`, `order_date`, `order_total`, `order_status`. A correct result contains 14 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q3. Task: Join the proposed fact and dimension outputs to summarize revenue by region. Required output: return only these columns in this order: `region`, `order_count`, `order_revenue`. A correct result contains 4 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q4. Task: Validate that the dimension key remains unique and report any duplicates. Required output: return only these columns in this order: `customer_id`, `duplicate_count`. A correct result contains 0 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------

