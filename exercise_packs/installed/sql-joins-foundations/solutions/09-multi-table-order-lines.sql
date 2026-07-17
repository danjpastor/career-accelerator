SELECT
    o.order_id,
    c.customer_name,
    p.product_name,
    oi.quantity,
    oi.quantity * oi.unit_price AS line_total
FROM orders AS o
INNER JOIN customers AS c
    ON o.customer_id = c.customer_id
INNER JOIN order_items AS oi
    ON o.order_id = oi.order_id
INNER JOIN products AS p
    ON oi.product_id = p.product_id
ORDER BY o.order_id, p.product_id;
