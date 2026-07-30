-- DuckDB Exercise 02: Select, rename, and calculate order fields
-- Read README.md before starting.
-- Save your completed copy under practice/duckdb/submissions/


-- -----------------------------------------------------------------

-- Q1. Task: Return every order with order ID, quantity, unit price, and a calculated pre-discount line value. Required output: return only these columns in this order: `order_id`, `quantity`, `unit_price`, `line_value`. A correct result contains 24 rows. Do not include extra columns; keep every filter and sort rule stated in the task.

SELECT order_id, quantity, unit_price, (unit_price*quantity) AS line_value
FROM ex02_retail_orders;

-- -----------------------------------------------------------------

-- Q2. Task: Return every order with concise aliases for region, channel, and recorded revenue. Required output: return only these columns in this order: `order_id`, `sales_region`, `channel`, `recorded_revenue`. A correct result contains 24 rows. Do not include extra columns; keep every filter and sort rule stated in the task.

-- Write and run your query below this comment.

-- -----------------------------------------------------------------

-- Q3. Task: Return each order with its recorded revenue and the difference between recorded revenue and quantity multiplied by unit price. Required output: return only these columns in this order: `order_id`, `recorded_revenue`, `revenue_difference`. A correct result contains 24 rows. Do not include extra columns; keep every filter and sort rule stated in the task.

-- Write and run your query below this comment.

-- -----------------------------------------------------------------

-- Q4. Task: Return the distinct combinations of region and sales channel, ordered consistently. Required output: return only these columns in this order: `region`, `sales_channel`. A correct result contains 12 rows. Do not include extra columns; keep every filter and sort rule stated in the task.

-- Write and run your query below this comment.

-- -----------------------------------------------------------------
