SELECT
    d.department_name,
    COUNT(DISTINCT e.employee_id) AS employee_count,
    COUNT(DISTINCT (a.project_id, a.employee_id)) AS assignment_count
FROM departments AS d
LEFT JOIN employees AS e
    ON d.department_id = e.department_id
LEFT JOIN project_assignments AS a
    ON e.employee_id = a.employee_id
GROUP BY d.department_name
ORDER BY d.department_name;
