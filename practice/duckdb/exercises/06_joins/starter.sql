-- DuckDB Exercise 06: Combine customers, orders, and payments
-- Source instructions: README.md
-- Save your completed copy under practice/duckdb/submissions/

-- Confirm the relevant tables exist.
DESCRIBE ex06_customers;
DESCRIBE ex06_orders;
DESCRIBE ex06_payments;


-- -----------------------------------------------------------------
-- Q1. Task: INNER JOIN customers to orders and return customer name with each order. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q2. Task: LEFT JOIN customers to orders so customers without orders remain visible. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q3. Task: Find customers with no orders. Required output: return only these columns in this order: `customer_id`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q4. Task: Join orders to payments and identify orders with no payment. Required output: return only these columns in this order: `order_id`. A correct result contains 2 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q5. Task: Create a three-table result with customer, order total, payment amount, and payment method. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q6. Task: Calculate delivered-order revenue by region. Required output: return only these columns in this order: `region`, `sum(o.order_total)`. Use these exact names for calculated or summarized columns: `sum(o.order_total)`. A correct result contains 4 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q7. Task: Calculate customer lifetime delivered revenue, including customers with zero. Required output: return only these columns in this order: `customer_id`, `revenue`. Use these exact names for calculated or summarized columns: `revenue`. A correct result contains 10 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------
