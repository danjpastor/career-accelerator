SELECT customer_id, total_spent
FROM (
    SELECT customer_id, SUM(amount) AS total_spent
    FROM orders
    WHERE status = 'Completed'
    GROUP BY customer_id
) AS customer_totals
WHERE total_spent > (
    SELECT AVG(customer_total)
    FROM (
        SELECT customer_id, SUM(amount) AS customer_total
        FROM orders
        WHERE status = 'Completed'
        GROUP BY customer_id
    ) AS average_input
)
ORDER BY total_spent DESC;
