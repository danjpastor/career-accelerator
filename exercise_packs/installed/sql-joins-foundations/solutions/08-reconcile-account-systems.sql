SELECT
    COALESCE(c.account_id, b.account_id) AS account_id,
    c.account_name AS crm_name,
    b.billing_name,
    CASE
        WHEN c.account_id IS NOT NULL AND b.account_id IS NOT NULL THEN 'Matched'
        WHEN c.account_id IS NOT NULL THEN 'CRM only'
        ELSE 'Billing only'
    END AS source_status
FROM crm_accounts AS c
FULL OUTER JOIN billing_accounts AS b
    ON c.account_id = b.account_id
ORDER BY account_id;
