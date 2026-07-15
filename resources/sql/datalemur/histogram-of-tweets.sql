-- Problem: Histogram of Tweets
-- Difficulty: Easy
-- Topic: 
-- Concepts: CTE, GROUP BY

-- My solution:
WITH tweets_per_user AS (
    SELECT
        user_id,
        COUNT(*) AS tweet_bucket
    FROM tweets
    WHERE tweet_date >= '2022-01-01'
      AND tweet_date < '2023-01-01'
    GROUP BY user_id
)

SELECT
    tweet_bucket,
    COUNT(*) AS users_num
FROM tweets_per_user
GROUP BY tweet_bucket
ORDER BY tweet_bucket;
