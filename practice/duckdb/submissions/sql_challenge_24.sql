SELECT
    customer_id,
    CONCAT(UPPER(last_name),', ', LOWER(first_name)) AS export_name
FROM customers
ORDER BY customer_id
