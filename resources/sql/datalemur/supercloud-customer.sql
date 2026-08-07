-- Problem: Supercloud Customer
-- Platform: DataLemur
-- Difficulty: Medium
-- Topic: Relational Division
-- Required concepts: COUNT DISTINCT

-- Write and test your own solution below.
-- Record assumptions and validation checks as comments.

SELECT
  customer_id
FROM 
(SELECT
  customer_id,
  COUNT(DISTINCT product_category) AS count_category
FROM (SELECT
  c.customer_id,
  c.product_id,
  p.product_category
FROM customer_contracts AS c
  LEFT JOIN products AS p ON p.product_id = c.product_id
ORDER BY c.customer_id) jt
GROUP BY customer_id) cat_count
WHERE count_category = 3
