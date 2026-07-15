-- DuckDB Exercise 05: Segment service performance
-- Source instructions: README.md
-- Save your completed copy under practice/duckdb/submissions/

-- Confirm the relevant tables exist.
DESCRIBE ex05_service_requests;


-- -----------------------------------------------------------------
-- Q1. Create an SLA target with CASE: Critical 2h, High 4h, Medium 8h, Low 12h.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q2. Create an `sla_status` of `Met` or `Missed` by comparing first response to the target.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q3. Count requests by department and SLA status.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q4. Calculate SLA compliance percentage by department.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q5. Create resolution bands: `Fast` under 12 hours, `Standard` from 12 through 24, and `Slow` over 24.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q6. Return average CSAT by resolution band.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q7. Return reopened request count and reopen rate by department.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------
