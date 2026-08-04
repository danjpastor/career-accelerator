-- Problem: Page With No Likes
-- Platform: DataLemur
-- Difficulty: Easy
-- Topic: Joins
-- Required concepts: LEFT JOIN, NULL

-- Write and test your own solution below.
-- Record assumptions and validation checks as comments.

SELECT
  p.page_id
FROM pages as p
  LEFT JOIN page_likes AS l ON p.page_id = l.page_id
WHERE l.liked_date IS NULL
ORDER BY p.page_id ASC
