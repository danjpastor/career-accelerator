SELECT
    c.customer_id,
    c.customer_name,
    r.region_name
FROM customers AS c
INNER JOIN regions AS r
    ON c.region_id = r.region_id
ORDER BY c.customer_id;
