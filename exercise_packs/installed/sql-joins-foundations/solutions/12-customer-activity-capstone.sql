SELECT
    c.customer_id,
    c.customer_name,
    COALESCE(r.region_name, 'Unassigned') AS region_name,
    COUNT(DISTINCT CASE
        WHEN o.status = 'Completed' THEN o.order_id
    END) AS completed_order_count,
    SUM(CASE
        WHEN o.status = 'Completed' THEN o.total_amount
        ELSE 0
    END) AS completed_revenue,
    MAX(o.order_date) AS latest_order_date
FROM customers AS c
LEFT JOIN regions AS r
    ON c.region_id = r.region_id
LEFT JOIN orders AS o
    ON c.customer_id = o.customer_id
GROUP BY
    c.customer_id,
    c.customer_name,
    r.region_name
ORDER BY c.customer_id;
