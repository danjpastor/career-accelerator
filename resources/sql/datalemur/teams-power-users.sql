-- Problem: Teams Power Users
-- Platform: DataLemur
-- Difficulty: Easy
-- Topic: Aggregation
-- Required concepts: COUNT, ORDER BY

-- Write and test your own solution below.
-- Record assumptions and validation checks as comments.

SELECT sender_id, COUNT(*)
FROM messages
WHERE EXTRACT(YEAR FROM sent_date) = 2022 AND EXTRACT(MONTH FROM sent_date) = 8
GROUP BY sender_id
ORDER BY COUNT(*) DESC
LIMIT 2;
