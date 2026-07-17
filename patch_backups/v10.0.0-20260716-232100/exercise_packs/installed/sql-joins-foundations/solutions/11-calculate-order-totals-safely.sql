SELECT
    o.order_id,
    COUNT(oi.order_item_id) AS line_count,
    SUM(oi.quantity * oi.unit_price) AS calculated_order_total
FROM orders AS o
INNER JOIN order_items AS oi
    ON o.order_id = oi.order_id
GROUP BY o.order_id
ORDER BY o.order_id;
