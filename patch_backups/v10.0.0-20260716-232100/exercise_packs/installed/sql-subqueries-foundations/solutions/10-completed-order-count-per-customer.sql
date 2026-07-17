SELECT
    c.customer_name,
    (
        SELECT COUNT(*)
        FROM orders AS o
        WHERE o.customer_id = c.customer_id
          AND o.status = 'Completed'
    ) AS completed_order_count
FROM customers AS c
ORDER BY completed_order_count DESC, c.customer_name;
