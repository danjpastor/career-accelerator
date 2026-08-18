WITH user_activity AS (
SELECT
    user_id,
    DATE_TRUNC('month', event_time) AS activity_month,
    MIN(DATE_TRUNC('month', event_time)) OVER(PARTITION BY user_id) AS first_activity_month
FROM user_events)

SELECT
    activity_month,
    COUNT(CASE WHEN activity_month = first_activity_month THEN 1 END) AS new_users,
    COUNT(CASE WHEN activity_month != first_activity_month THEN 1 END) AS existing_users
FROM user_activity
GROUP BY activity_month
ORDER BY activity_month
