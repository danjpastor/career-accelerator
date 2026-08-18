-- Problem: User Shopping Sprees
-- Platform: DataLemur
-- Difficulty: Medium
-- Topic: Date Logic
-- Required concepts: GROUP BY, dates

-- Write and test your own solution below.
-- Record assumptions and validation checks as comments.

WITH numbered AS (
SELECT
  user_id,
  transaction_date,
  ROW_NUMBER() OVER(PARTITION BY user_id ORDER BY transaction_date) AS row_number
FROM transactions),

dateGroups AS (
SELECT
  user_id,
  transaction_date,
  (transaction_date - row_number * INTERVAL '1 day') as sub_date
FROM numbered)

SELECT
  user_id
FROM dateGroups
GROUP BY user_id, sub_date
HAVING COUNT(*) >= 3
ORDER BY user_id
