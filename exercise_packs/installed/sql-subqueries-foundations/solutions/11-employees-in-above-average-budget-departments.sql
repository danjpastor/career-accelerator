SELECT employee_name, department_id, salary
FROM employees
WHERE department_id IN (
    SELECT department_id
    FROM departments
    WHERE budget > (
        SELECT AVG(budget)
        FROM departments
    )
)
ORDER BY department_id, salary DESC;
