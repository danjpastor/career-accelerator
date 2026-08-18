SELECT
    case_id,
    subject
FROM support_cases
WHERE subject ILIKE '%CHARGE%'
