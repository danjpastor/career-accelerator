SELECT
    metric_id,
    metric_value
FROM raw_metrics
WHERE TRY_CAST(TRIM(metric_value) AS DECIMAL(12,2)) IS NULL
