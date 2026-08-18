SELECT
    customer_id,
    REGEXP_REPLACE(phone, '[^0-9]', '', 'g') AS phone_digits
FROM customers
WHERE phone IS NOT NULL
ORDER BY customer_id
