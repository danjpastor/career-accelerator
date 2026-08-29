SELECT
    COUNT(*) AS total_rows,
    SUM(CASE WHEN email IS NULL THEN 1 ELSE 0 END) AS missing_emails,
    COUNT(email) - COUNT(DISTINCT email) AS duplicate_email_rows
 FROM raw_contacts
