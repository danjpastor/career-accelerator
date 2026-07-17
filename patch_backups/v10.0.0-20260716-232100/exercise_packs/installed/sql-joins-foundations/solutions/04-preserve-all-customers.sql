SELECT
    c.customer_id,
    c.customer_name,
    o.order_id,
    o.status
FROM customers AS c
LEFT JOIN orders AS o
    ON c.customer_id = o.customer_id
ORDER BY c.customer_id, o.order_id;
