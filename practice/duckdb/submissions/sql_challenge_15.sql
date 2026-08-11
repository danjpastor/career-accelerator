SELECT
    team,
    session_date,
    employee_id,
    ROW_NUMBER() OVER(PARTITION BY team ORDER BY session_date,session_id) AS team_session_number
FROM work_sessions
ORDER BY team, team_session_number
