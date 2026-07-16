-- Problem: Data Science Skills
-- Platform: DataLemur
-- Difficulty: Easy
-- Topic: Aggregation
-- Required concepts: GROUP BY, HAVING

-- Write and test your own solution below.
-- Record assumptions and validation checks as comments.

-- My solution:

SELECT candidate_id
FROM candidates
WHERE skill IN ('PostgreSQL','Tableau', 'Python')
GROUP BY candidate_id
HAVING COUNT(*) = 3


