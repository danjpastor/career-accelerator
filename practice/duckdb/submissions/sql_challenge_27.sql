SELECT
    product_id,
    product_name,
    ROUND(AVG(unit_price),2) AS average_price,
    MIN(unit_price) AS min_price,
    MAX(unit_price) AS max_price,
    max_price - min_price AS price_range
FROM raw_order_lines
GROUP BY product_id, product_name
ORDER BY product_id
