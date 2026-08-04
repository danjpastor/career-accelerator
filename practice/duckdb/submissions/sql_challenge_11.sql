SELECT
    order_id,
    total_amount,
    CASE WHEN total_amount < 100 THEN 'Small'
             WHEN total_amount >= 100 AND total_amount <= 299.99 THEN 'Standard'
             ELSE 'Large' END AS order_size
    FROM orders
    WHERE status = 'Completed'
    ORDER BY order_id;
