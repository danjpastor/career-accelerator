-- Problem: Laptop vs. Mobile Viewership
-- Platform: DataLemur
-- Difficulty: Easy
-- Topic: Conditional Logic
-- Required concepts: CASE, COUNT

-- Write and test your own solution below.
-- Record assumptions and validation checks as comments.

SELECT 
  COUNT(CASE WHEN device_type = 'laptop' THEN user_id END) AS laptop_views,
  COUNT(CASE WHEN device_type = 'tablet' OR device_type = 'phone' THEN user_id END) AS mobile_views
FROM viewership;
