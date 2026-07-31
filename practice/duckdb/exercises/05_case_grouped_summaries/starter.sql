-- DuckDB Exercise 11: Segment service performance
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
-- Q3. Show how many service requests met or missed the SLA in each department. Return `department`, `sla_status`, and the count as `request_count`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q4. Calculate the percentage of requests that met the SLA in each department. Round to two decimal places and name it `sla_compliance_pct`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q5. Group requests into `Fast` under 12 hours, `Standard` from 12 through 24 hours, and `Slow` over 24 hours. Return each `resolution_band` and its `request_count`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q6. Compare customer satisfaction across the three resolution bands. Return `resolution_band` and average `csat_score` rounded to two decimal places as `average_csat`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q7. For each department, count reopened requests and calculate the reopen rate as a percentage. Return `reopened_requests` and `reopen_rate_pct`, rounded to two decimal places.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------
