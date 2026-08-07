-- Career Accelerator Applied Lab 04
-- Fix a join that duplicates revenue

-- Applied Lab 04: Fix a join that duplicates revenue
-- Concepts: join cardinality, grain, duplicate amplification, reconciliation

-- Broken query: multiple return rows amplify order revenue.
SELECT c.region, SUM(o.quantity * p.unit_price) AS revenue
FROM orders o
JOIN customers c USING (customer_id)
JOIN products p USING (product_id)
LEFT JOIN returns r USING (order_id)
WHERE o.status = 'Completed'
GROUP BY c.region;

-- TODO: add corrected analysis and validation queries.
