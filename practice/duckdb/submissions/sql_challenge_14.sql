SELECT
    customer_id,
    CONCAT(first_name, ' ', last_name) AS customer_name,
    COUNT(*) OVER() AS total_customers
FROM customers
ORDER BY customer_id
