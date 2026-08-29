WITH gap_orders AS (
    SELECT
    order_id,
    order_date,
    LAG(order_date) OVER(ORDER BY order_date) AS previous_order_date,
    DATEDIFF('day', previous_order_date, order_date) AS gap_days
FROM account_orders
)

SELECT *
FROM gap_orders
WHERE gap_days > 1
ORDER BY order_date, order_id
