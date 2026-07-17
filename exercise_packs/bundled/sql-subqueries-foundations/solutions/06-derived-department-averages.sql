SELECT department_id, avg_salary
FROM (
    SELECT department_id, ROUND(AVG(salary), 2) AS avg_salary
    FROM employees
    GROUP BY department_id
) AS department_summary
WHERE avg_salary > 80000
ORDER BY avg_salary DESC;
