SELECT
    r.region_name,
    p.product_name
FROM regions AS r
CROSS JOIN products AS p
ORDER BY r.region_id, p.product_id;
