SELECT
    r.region_id,
    r.region_name,
    COUNT(c.customer_id) AS customer_count
FROM regions AS r
LEFT JOIN customers AS c
    ON r.region_id = c.region_id
GROUP BY r.region_id, r.region_name
ORDER BY r.region_id;
