-- Applied Lab 17: Fix denominator, date-filter, and grain errors
-- Concepts: KPI denominator, inclusive dates, weighted rates, analysis grain

-- Broken KPI: average of row-level rates and ambiguous date boundaries.
SELECT strftime(order_date, '%Y-%m') AS month,
       AVG(return_quantity * 1.0 / quantity) AS return_rate
FROM read_csv_auto('practice/applied/datasets/operations/orders.csv') o
LEFT JOIN read_csv_auto('practice/applied/datasets/operations/returns.csv') r USING (order_id)
WHERE order_date BETWEEN '2026-01-01' AND '2026-03-31'
GROUP BY 1;

-- TODO: add corrected analysis and validation queries.
