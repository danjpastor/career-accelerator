-- DuckDB Exercise 06: Join customers, orders, and payments
-- Source instructions: README.md
-- Save your completed copy under practice/duckdb/submissions/

-- Confirm the relevant tables exist.
DESCRIBE ex06_customers;
DESCRIBE ex06_orders;
DESCRIBE ex06_payments;


-- -----------------------------------------------------------------
-- Q1. Check how many orders have a matching customer record. Use an inner join and return the count as `matched_orders`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q2. Check that a left join keeps customers who have no orders. Return the number of rows produced by the join as `customer_order_rows`.
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
-- Q5. Join customers, orders, and payments, then count the rows in the combined result. Return the count as `joined_payment_rows`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q6. Show delivered-order revenue by customer region. Return `region` and the total as `delivered_revenue`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q7. Calculate customer lifetime delivered revenue, including customers with zero.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------
