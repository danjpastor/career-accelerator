-- DuckDB Exercise 06: Combine customers, orders, and payments
-- Source instructions: README.md
-- Save your completed copy under practice/duckdb/submissions/

-- Confirm the relevant tables exist.
DESCRIBE ex06_customers;
DESCRIBE ex06_orders;
DESCRIBE ex06_payments;


-- -----------------------------------------------------------------

-- Q1. Check how many orders have a matching customer record. Use an inner join and return the count as `matched_orders`.

SELECT
    COUNT(*) AS matched_orders
FROM ex06_customers AS c
    INNER JOIN ex06_orders AS o ON c.customer_id = o.customer_id

-- -----------------------------------------------------------------

-- Q2. Check that a left join keeps customers who have no orders. Return the number of rows produced by the join as `customer_order_rows`.

SELECT
    COUNT(*) AS customer_order_rows
FROM ex06_customers AS c
    LEFT JOIN ex06_orders AS o ON o.customer_id = c.customer_id

-- -----------------------------------------------------------------

-- Q3. Find customers with no orders.

SELECT
    c.customer_id
FROM ex06_customers AS c
    LEFT JOIN ex06_orders AS o ON o.customer_id = c.customer_id
WHERE order_id IS NULL

-- -----------------------------------------------------------------

-- Q4. Join orders to payments and identify orders with no payment.

SELECT
    o.order_id AS order_id
FROM ex06_orders AS o
    LEFT JOIN ex06_payments AS p ON o.order_id = p.order_id
WHERE p.payment_date IS NULL

-- -----------------------------------------------------------------

-- Q5. Join customers, orders, and payments, then count the rows in the combined result. Return the count as `joined_payment_rows`.

SELECT
    COUNT(*) AS joined_payment_rows
FROM ex06_orders AS o
    LEFT JOIN ex06_payments AS p ON p.order_id = o.order_id
    LEFT JOIN ex06_customers AS c ON c.customer_id = o.customer_id

-- -----------------------------------------------------------------

-- Q6. Show delivered-order revenue by customer region. Return `region` and the total as `delivered_revenue`.

SELECT
    c.region AS region,
    SUM(o.order_total) AS delivered_revenue
FROM ex06_customers AS c
    INNER JOIN ex06_orders AS o ON c.customer_id = o.customer_id
WHERE o.order_status = 'Delivered'
GROUP BY region

-- -----------------------------------------------------------------

-- Q7. Calculate customer lifetime delivered revenue, including customers with zero.

SELECT
    c.customer_id AS customer_id,
    COALESCE(SUM(o.order_total), 0) AS revenue
FROM ex06_customers AS c
    LEFT JOIN ex06_orders AS o ON c.customer_id = o.customer_id
    AND o.order_status = 'Delivered'
GROUP BY c.customer_id
ORDER BY c.customer_id

-- -----------------------------------------------------------------
