-- DuckDB Exercise 08: Analyze a VFX production snapshot
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
-- Q2. Calculate actual logged hours per shot.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q3. Compare estimated and actual hours for completed shots.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q4. Calculate on-time completion rate by department.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q5. Create a risk flag using status, due date, revision count, and hours variance.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q6. Summarize estimated hours, actual hours, and revisions by project.
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
