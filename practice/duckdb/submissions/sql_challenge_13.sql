WITH repeat_customers AS 
(SELECT
    customer_id,
    COUNT(*) AS order_count,
    SUM(total_amount) AS order_value
FROM orders
WHERE status = 'Completed'
GROUP BY customer_id
HAVING order_value >= 400 AND order_count > 1)

SELECT 
    DISTINCT o.customer_id,
    CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
    repeat_customers.order_count AS completed_orders,
    ROUND(repeat_customers.order_value, 2) AS completed_value
FROM orders AS o
    INNER JOIN repeat_customers ON o.customer_id = repeat_customers.customer_id
    INNER JOIN customers AS c ON c.customer_id = o.customer_id
ORDER BY completed_value DESC, o.customer_id
