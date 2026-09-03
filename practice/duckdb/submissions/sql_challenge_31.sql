WITH combined AS 
(SELECT
    w.worker_id,
    w.worker_name,
    t.team_name,
    w.hourly_rate,
    (s.regular_hours + s.overtime_hours) AS hours_worked,
    ROUND((SUM(s.regular_hours) * w.hourly_rate),2) AS regular_worked,
    ROUND(((SUM(s.overtime_hours) * w.hourly_rate) * 1.5),2) AS overtime_worked,
    regular_worked + overtime_worked AS total_worked
FROM shifts AS s
LEFT JOIN workers AS w
ON w.worker_id = s.worker_id
LEFT JOIN teams AS t
ON t.team_id = w.team_id
GROUP BY w.worker_id, w.worker_name, t.team_name, hours_worked, w.hourly_rate)

SELECT
    team_name,
    COUNT(DISTINCT worker_id) AS worker_count,
    SUM(hours_worked) AS total_hours,
    SUM(total_worked) AS total_labor_cost
FROM combined
GROUP BY team_name
ORDER BY total_labor_cost DESC, team_name
