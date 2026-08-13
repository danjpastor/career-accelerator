-- Problem: Second Highest Salary
-- Platform: DataLemur
-- Difficulty: Medium
-- Topic: Ranking
-- Required concepts: DENSE_RANK

-- Write and test your own solution below.
-- Record assumptions and validation checks as comments.

WITH ranked_salaries AS (
SELECT
  salary,
  DENSE_RANK() OVER(ORDER BY salary DESC)
FROM employee)

SELECT
  salary AS second_highest_salary
FROM ranked_salaries
WHERE dense_rank = 2;
