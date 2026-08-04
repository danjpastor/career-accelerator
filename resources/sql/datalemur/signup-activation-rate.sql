-- Problem: Signup Activation Rate
-- Platform: DataLemur
-- Difficulty: Medium
-- Topic: Joins
-- Required concepts: JOIN, ratios

-- Write and test your own solution below.
-- Record assumptions and validation checks as comments.

SELECT
  ROUND(AVG(CASE WHEN t.signup_action = 'Confirmed' THEN 1 ELSE 0 END), 2) AS confirm_rate
FROM texts AS t
  LEFT JOIN emails AS e ON t.email_id = e.email_id
