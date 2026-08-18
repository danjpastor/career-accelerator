-- Problem: Top Three Salaries
-- Platform: DataLemur
-- Difficulty: Medium
-- Topic: Ranking
-- Required concepts: PARTITION BY

-- Write and test your own solution below.
-- Record assumptions and validation checks as comments.

WITH ranked_salaries AS (
SELECT
  d.department_name,
  e.name,
  e.salary,
  DENSE_RANK() OVER (PARTITION BY d.department_name ORDER BY e.salary DESC) AS salary_rank
FROM employee AS e
  LEFT JOIN department AS d ON d.department_id = e.department_id
ORDER BY d.department_name, e.salary DESC, e.name)

SELECT
  department_name,
  name,
  salary
FROM ranked_salaries
WHERE salary_rank IN (1,2,3)
