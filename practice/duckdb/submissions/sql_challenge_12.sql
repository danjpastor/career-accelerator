SELECT
    order_id,
    customer_id,
    total_amount
FROM orders
WHERE total_amount > (
    SELECT
    AVG(total_amount)
FROM orders
WHERE status = 'Completed'
) AND status = 'Completed'
ORDER BY total_amount DESC, order_id
