-- DuckDB Exercise 07: Use outer, cross, and self joins
-- Read README.md before starting.
-- Save your completed copy under practice/duckdb/submissions/


-- -----------------------------------------------------------------

-- Q1. Use a left join to show every customer and any related orders, keeping customers with no order.

SELECT
    c.customer_id AS customer_id,
    c.customer_name AS customer_name,
    o.order_id AS order_id,
    o.order_total AS order_total
FROM ex06_customers AS c
    LEFT JOIN ex06_orders AS o ON c.customer_id = o.customer_id
ORDER BY c.customer_id

-- -----------------------------------------------------------------

-- Q2. Use a full join to identify customer IDs that appear on only one side of the customer-order relationship.

SELECT
    c.customer_id AS customer_id,
    c.customer_name AS customer_name,
    o.order_id AS order_id,
FROM ex06_customers AS c
    FULL JOIN ex06_orders AS o ON o.customer_id = c.customer_id

-- -----------------------------------------------------------------

-- Q3. Use a self join to show each employee beside their manager name when one exists.

-- Write and run your query below this comment.

-- -----------------------------------------------------------------

-- Q4. Use a cross join to build every combination of department and two named planning scenarios.

-- Write and run your query below this comment.

-- -----------------------------------------------------------------
