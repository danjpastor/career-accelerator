SELECT c.customer_name, s.completed_orders, s.total_spent
FROM customers AS c
JOIN (
    SELECT customer_id,
           COUNT(*) AS completed_orders,
           SUM(amount) AS total_spent
    FROM orders
    WHERE status = 'Completed'
    GROUP BY customer_id
) AS s
    ON s.customer_id = c.customer_id
WHERE s.completed_orders >= 2
  AND s.total_spent > (
      SELECT AVG(customer_total)
      FROM (
          SELECT customer_id, SUM(amount) AS customer_total
          FROM orders
          WHERE status = 'Completed'
          GROUP BY customer_id
      ) AS totals_for_average
  )
ORDER BY s.total_spent DESC;
