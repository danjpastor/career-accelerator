SELECT
    shot_id,
    project_id,
    department,
    CASE WHEN delivery_date > deadline THEN 'Late'
    ELSE 'On Time' END AS delivery_status,
    (actual_hours - estimated_hours) AS hours_variance
FROM vfx_shots
WHERE status = 'Final'
ORDER BY project_id, shot_id
