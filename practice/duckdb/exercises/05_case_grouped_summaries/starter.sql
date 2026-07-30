-- DuckDB Exercise 11: Group service results with CASE
-- Source instructions: README.md
-- Save your completed copy under practice/duckdb/submissions/

-- Confirm the relevant tables exist.
DESCRIBE ex05_service_requests;


-- -----------------------------------------------------------------
-- Q1. Task: Create an SLA target with CASE: Critical 2h, High 4h, Medium 8h, Low 12h. Required output: return only these columns in this order: `severity`, `target`. Use these exact names for calculated or summarized columns: `target`. A correct result contains 4 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q2. Task: Create an `sla_status` of `Met` or `Missed` by comparing first response to the target. Required output: return only these columns in this order: `met`, `missed`. Use these exact names for calculated or summarized columns: `met`, `missed`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q3. Task: Count requests by department and SLA status. Required output: return only these columns in this order: `department`, `sla_status`, `count_star()`. Use these exact names for calculated or summarized columns: `sla_status`, `count_star()`. A correct result contains 6 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q4. Task: Calculate SLA compliance percentage by department. Required output: return only these columns in this order: `department`, `round(((100.0 * sum(CASE  WHEN ((first_response_hours <= CASE  WHEN ((severity = 'Critical')) THEN (2) WHEN ((severity = 'High')) THEN (4) WHEN ((severity = 'Medium')) THEN (8) ELSE 12 END)) THEN (1) ELSE 0 END)) / count_star()), 2)`. Use these exact names for calculated or summarized columns: `round(((100.0 * sum(CASE  WHEN ((first_response_hours <= CASE  WHEN ((severity = 'Critical')) THEN (2) WHEN ((severity = 'High')) THEN (4) WHEN ((severity = 'Medium')) THEN (8) ELSE 12 END)) THEN (1) ELSE 0 END)) / count_star()), 2)`. A correct result contains 3 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q5. Task: Create resolution bands: `Fast` under 12 hours, `Standard` from 12 through 24, and `Slow` over 24. Required output: return only these columns in this order: `band`, `count_star()`. Use these exact names for calculated or summarized columns: `band`, `count_star()`. A correct result contains 3 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q6. Task: Return average CSAT by resolution band. Required output: return only these columns in this order: `band`, `round(avg(csat_score), 2)`. Use these exact names for calculated or summarized columns: `band`, `round(avg(csat_score), 2)`. A correct result contains 3 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q7. Task: Return reopened request count and reopen rate by department. Required output: return only these columns in this order: `department`, `sum(CASE  WHEN ((reopened = 'Yes')) THEN (1) ELSE 0 END)`, `round(((100.0 * sum(CASE  WHEN ((reopened = 'Yes')) THEN (1) ELSE 0 END)) / count_star()), 2)`. Use these exact names for calculated or summarized columns: `sum(CASE  WHEN ((reopened = 'Yes')) THEN (1) ELSE 0 END)`, `round(((100.0 * sum(CASE  WHEN ((reopened = 'Yes')) THEN (1) ELSE 0 END)) / count_star()), 2)`. A correct result contains 3 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------
