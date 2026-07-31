-- DuckDB Exercise 30: Analyze a VFX production snapshot
-- Source instructions: README.md
-- Save your completed copy under practice/duckdb/submissions/

-- Confirm the relevant tables exist.
DESCRIBE ex08_projects;
DESCRIBE ex08_shots;
DESCRIBE ex08_time_entries;


-- -----------------------------------------------------------------
-- Q1. Find unfinished shots due before June 30, 2026.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q2. Show actual logged hours for each shot. Return `shot_id` and total hours as `actual_hours`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q3. Count completed shots whose actual logged hours exceeded their estimate. Return the result as `over_estimate_shots`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q4. Calculate the on-time completion percentage for each department. Round to two decimal places and name it `on_time_completion_pct`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q5. Count unfinished shots that are overdue, have at least three revisions, or have logged more hours than estimated. Return the count as `risk_shots`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q6. Summarize workload by project. Return `project_id`, total `estimated_hours`, total `actual_hours`, and total `revisions`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q7. Rank artists by total logged hours using `DENSE_RANK`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q8. Return the highest-risk project and explain the drivers in two sentences.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------
