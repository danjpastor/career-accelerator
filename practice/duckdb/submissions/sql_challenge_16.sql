SELECT
    employee_id,
    ROUND(SUM(hours), 1) AS total_hours,
    RANK() OVER(ORDER BY SUM(hours) DESC) AS hours_rank
FROM work_sessions
GROUP BY employee_id
