-- DuckDB Exercise 05: Join orders to customers
-- Read README.md before starting.
-- Save your completed copy under practice/duckdb/submissions/


-- -----------------------------------------------------------------

-- Q1. Join orders to customers and return one row per matched order with customer name and region.

SELECT
    o.order_id AS order_id,
    c.customer_name AS customer_name,
    c.region AS region,
    o.order_total AS order_total
FROM ex06_customers AS c
    INNER JOIN ex06_orders AS o ON c.customer_id = o.customer_id

-- -----------------------------------------------------------------

-- Q2. Return only delivered orders after joining orders to customers.

SELECT
    o.order_id AS order_id,
    c.customer_name AS customer_name,
    o.order_status AS order_status
FROM ex06_customers AS c
    LEFT JOIN ex06_orders AS o ON o.customer_id = c.customer_id
WHERE o.order_status = 'Delivered';

-- -----------------------------------------------------------------

-- Q3. Join payments to orders and return the payment amount beside the order total.

SELECT
    p.payment_id AS payment_id,
    o.order_id AS order_id,
    p.amount AS amount,
    o.order_total AS order_total
FROM ex06_orders AS o
    INNER JOIN ex06_payments AS p ON o.order_id = p.order_id

-- -----------------------------------------------------------------

-- Q4. Summarize matched order revenue by customer region.

SELECT
    c.region AS region,
    COUNT(*) AS order_count,
    SUM(o.order_total) AS order_revenue
FROM ex06_orders AS o
    INNER JOIN ex06_customers AS c ON c.customer_id = o.customer_id
GROUP BY region
ORDER BY order_revenue DESC

-- -----------------------------------------------------------------
