-- Applied Lab 16: Diagnose duplicated revenue from a broken join
-- Concepts: join cardinality, grain, duplicate amplification, reconciliation

-- Broken query: multiple return rows amplify order revenue.
SELECT c.region, SUM(o.quantity * p.unit_price) AS revenue
FROM read_csv_auto('practice/applied/datasets/operations/orders.csv') o
JOIN read_csv_auto('practice/applied/datasets/operations/customers.csv') c USING (customer_id)
JOIN read_csv_auto('practice/applied/datasets/operations/products.csv') p USING (product_id)
LEFT JOIN read_csv_auto('practice/applied/datasets/operations/returns.csv') r USING (order_id)
WHERE o.status = 'Completed'
GROUP BY c.region;

-- TODO: add corrected analysis and validation queries.
