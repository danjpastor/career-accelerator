-- Problem: Odd and Even Measurements
-- Platform: DataLemur
-- Difficulty: Medium
-- Topic: Window Functions
-- Required concepts: ROW_NUMBER, SUM

-- Write and test your own solution below.
-- Record assumptions and validation checks as comments.

WITH ranked_measures AS (
SELECT
  CAST(measurement_time AS DATE) AS measurement_day,
  measurement_value,
  ROW_NUMBER() OVER(PARTITION BY CAST(measurement_time AS DATE) ORDER BY measurement_time) AS measurement_num
FROM measurements)

SELECT
  measurement_day,
  SUM(measurement_value) FILTER (WHERE measurement_num % 2 != 0) AS odd_sum, 
  SUM(measurement_value) FILTER (WHERE measurement_num % 2 = 0) AS even_sum 
FROM ranked_measures
GROUP BY measurement_day
ORDER BY measurement_day
