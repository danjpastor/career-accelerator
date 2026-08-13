-- Problem: User's Third Transaction
-- Platform: DataLemur
-- Difficulty: Medium
-- Topic: Window Functions
-- Required concepts: ROW_NUMBER

-- Write and test your own solution below.
-- Record assumptions and validation checks as comments.

WITH list AS (
SELECT
  user_id,
  spend,
  transaction_date,
  ROW_NUMBER() OVER(PARTITION BY user_id ORDER BY transaction_date)
FROM transactions)

SELECT
  user_id,
  spend,
  transaction_date
FROM list
WHERE row_number = 3
