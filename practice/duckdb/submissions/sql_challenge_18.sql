SELECT
    revenue_date,
    revenue,
    ROUND(
        AVG(revenue) OVER (
            ORDER BY revenue_date
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ),
        2
    ) AS three_day_average
FROM daily_revenue
ORDER BY revenue_date;
