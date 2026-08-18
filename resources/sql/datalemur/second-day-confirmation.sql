-- Problem: Second Day Confirmation
-- Platform: DataLemur
-- Difficulty: Medium
-- Topic: Joins
-- Required concepts: dates, filtering

-- Write and test your own solution below.
-- Record assumptions and validation checks as comments.

WITH confirmed_signups AS (
SELECT
  e.user_id,
  e.signup_date,
  t.action_date,
  t.signup_action
FROM emails AS e
  INNER JOIN texts AS t
  ON e.email_id = t.email_id
WHERE t.signup_action = 'Confirmed'
ORDER BY user_id),

second_day_confirmation AS (
SELECT
  user_id,
  COUNT(CASE WHEN action_date - INTERVAL '1 day' = signup_date THEN 1 END) AS second_confirmed
FROM confirmed_signups
GROUP BY user_id)

SELECT
  user_id
FROM second_day_confirmation
WHERE second_confirmed = 1
