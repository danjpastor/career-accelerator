SELECT
     CASE
        WHEN GROUPING(restaurant_name) = 1
            THEN 'ALL RESTAURANTS'
        ELSE restaurant_name
    END AS restaurant_name,
    ROUND(SUM(subtotal + service_fee),2) AS total_revenue
FROM restaurant_orders
GROUP BY ROLLUP(restaurant_name)
ORDER BY
    GROUPING(restaurant_name),
    restaurant_name;
