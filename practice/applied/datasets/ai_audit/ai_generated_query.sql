-- Intentionally flawed AI-generated query.
SELECT
    c.region,
    SUM(o.order_total) AS revenue,
    COUNT(r.return_id) * 1.0 / COUNT(*) AS return_rate
FROM orders o
JOIN customers c
  ON o.customer_id = c.customer_id
JOIN products p
  ON o.product_id = p.product_id
LEFT JOIN returns r
  ON o.order_id = r.order_id
WHERE o.status <> 'Cancelled'
GROUP BY c.region
ORDER BY revenue DESC;
