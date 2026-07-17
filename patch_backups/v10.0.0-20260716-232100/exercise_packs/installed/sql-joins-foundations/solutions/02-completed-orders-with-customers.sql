SELECT
    o.order_id,
    c.customer_name,
    o.total_amount
FROM orders AS o
INNER JOIN customers AS c
    ON o.customer_id = c.customer_id
WHERE o.status = 'Completed'
ORDER BY o.order_id;
