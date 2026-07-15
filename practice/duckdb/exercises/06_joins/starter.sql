-- DuckDB Exercise 06: Join customers, orders, and payments
-- Source instructions: README.md
-- Save your completed copy under practice/duckdb/submissions/

-- Confirm the relevant tables exist.
DESCRIBE ex06_customers;
DESCRIBE ex06_orders;
DESCRIBE ex06_payments;


-- -----------------------------------------------------------------
-- Q1. INNER JOIN customers to orders and return customer name with each order.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q2. LEFT JOIN customers to orders so customers without orders remain visible.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q3. Find customers with no orders.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q4. Join orders to payments and identify orders with no payment.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q5. Create a three-table result with customer, order total, payment amount, and payment method.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q6. Calculate delivered-order revenue by region.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q7. Calculate customer lifetime delivered revenue, including customers with zero.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------
