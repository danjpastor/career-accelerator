-- Problem: Tweets' Rolling Averages
-- Platform: DataLemur
-- Difficulty: Medium
-- Topic: Window Functions
-- Required concepts: AVG OVER

-- Write and test your own solution below.
-- Record assumptions and validation checks as comments.

SELECT
  user_id,
  tweet_date,
  ROUND(AVG(tweet_count) OVER(PARTITION BY user_id ORDER BY tweet_date ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS rolling_avg_3d
FROM tweets
ORDER BY user_id, tweet_date
