SELECT department_name, budget
FROM departments
WHERE budget > (
    SELECT AVG(budget)
    FROM departments
)
ORDER BY budget DESC;
