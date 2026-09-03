SELECT
    'duplicate_customer_ids' AS issue_type,
    COUNT(*) - COUNT(DISTINCT customer_id) AS issue_count
FROM audit_customers

UNION ALL

SELECT
    'missing_customer_emails' AS issue_type,
    COUNT(*) AS issue_count
FROM audit_customers
WHERE email IS NULL

UNION ALL

SELECT
    'orphaned_orders' AS issue_type,
    COUNT(*) AS issue_count
FROM audit_orders AS o
LEFT JOIN audit_customers AS c
    ON o.customer_id = c.customer_id
WHERE NOT EXISTS (
    SELECT 1
    FROM audit_customers AS c
    WHERE c.customer_id = o.customer_id
)

UNION ALL

SELECT
    'duplicate_order_ids' AS issue_type,
    COUNT(*) - COUNT(DISTINCT order_id) AS issue_count
FROM audit_orders

UNION ALL

SELECT
    'negative_order_amounts' AS issue_type,
    COUNT(*) AS issue_count
FROM audit_orders
WHERE amount < 0

ORDER BY issue_type;
