WITH task_sequence AS (
    SELECT
        start_date,
        end_date,
        LAG(end_date) OVER(ORDER BY start_date) AS previous_end
    FROM project_days
),

project_starts AS (
    SELECT
        start_date,
        end_date,
        previous_end,
        CASE
            WHEN start_date = previous_end THEN 0
            ELSE 1
        END AS new_project
    FROM task_sequence
),

project_ids AS (
SELECT
    start_date,
    end_date,
    previous_end,
    new_project,
    SUM(new_project) OVER(ORDER BY start_date) AS project_id
FROM project_starts)

SELECT
    MIN(start_date) AS project_start,
    MAX(end_date) AS project_end
FROM project_ids
GROUP BY project_id
ORDER BY (MAX(end_date) - MIN(start_date)), project_start
