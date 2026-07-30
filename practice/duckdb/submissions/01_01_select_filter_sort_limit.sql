-- DuckDB Exercise 01: Filter and sort support tickets
-- Source instructions: README.md
-- Save your completed copy under practice/duckdb/submissions/

-- Confirm the relevant tables exist.
DESCRIBE ex01_support_tickets;


-- -----------------------------------------------------------------

-- Q1. Task: Return `ticket_id`, `customer_name`, and `status` for every ticket. Required output: return only these columns in this order: `ticket_id`, `customer_name`, `status`. A correct result contains 20 rows. Do not include extra columns; keep every filter and sort rule stated in the task.

-- Write and run your query below this comment.

-- -----------------------------------------------------------------

-- Q2. Task: Return all tickets whose status is `Open`. Required output: return only these columns in this order: `ticket_id`. A correct result contains 6 rows. Do not include extra columns; keep every filter and sort rule stated in the task.

-- Write and run your query below this comment.

-- -----------------------------------------------------------------

-- Q3. Task: Return open or pending tickets with `High` or `Urgent` priority. Required output: return only these columns in this order: `ticket_id`. A correct result contains 5 rows. Do not include extra columns; keep every filter and sort rule stated in the task.

-- Write and run your query below this comment.

-- -----------------------------------------------------------------

-- Q4. Task: Return tickets created after June 15, 2026. Required output: return only these columns in this order: `ticket_id`. A correct result contains 10 rows. Do not include extra columns; keep every filter and sort rule stated in the task.

-- Write and run your query below this comment.

-- -----------------------------------------------------------------

-- Q5. Task: Return closed tickets ordered from longest to shortest `resolution_hours`. Required output: return only these columns in this order: `ticket_id`, `resolution_hours`. A correct result contains 11 rows. Do not include extra columns; keep every filter and sort rule stated in the task.

-- Write and run your query below this comment.

-- -----------------------------------------------------------------

-- Q6. Task: Return the five highest satisfaction scores among closed tickets; break ties by newest `created_at`. Required output: return only these columns in this order: `ticket_id`, `satisfaction_score`. A correct result contains 5 rows. Do not include extra columns; keep every filter and sort rule stated in the task.

-- Write and run your query below this comment.

-- -----------------------------------------------------------------

-- Q7. Task: Return open Billing tickets ordered from oldest to newest. Required output: return only these columns in this order: `ticket_id`. A correct result contains 4 rows. Do not include extra columns; keep every filter and sort rule stated in the task.

-- Write and run your query below this comment.

-- -----------------------------------------------------------------
