WITH ordered_specialists AS (
SELECT
    specialist_name,
    specialty,
    ROW_NUMBER() OVER(PARTITION BY specialty ORDER BY specialist_name) AS row_number
FROM specialists
ORDER BY specialty, specialist_name)

SELECT
    MAX(CASE WHEN specialty = 'Analyst' THEN specialist_name END) AS analyst,
    MAX(CASE WHEN specialty = 'Designer' THEN specialist_name END) AS designer,
    MAX(CASE WHEN specialty = 'Engineer' THEN specialist_name END) AS engineer,
    MAX(CASE WHEN specialty = 'Manager' THEN specialist_name END) AS manager
FROM ordered_specialists
GROUP BY row_number
ORDER BY row_number
