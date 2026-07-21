-- Problem: Pharmacy Analytics Part 1
-- Platform: DataLemur
-- Difficulty: Easy
-- Topic: Arithmetic
-- Required concepts: SUM, subtraction

-- Write and test your own solution below.
-- Record assumptions and validation checks as comments.

SELECT drug, SUM(total_sales-cogs) AS total_profit
FROM pharmacy_sales
GROUP BY drug
ORDER BY total_profit DESC
LIMIT 3;
