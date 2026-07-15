-- DuckDB Exercise 01: Filter and sort support tickets
-- Source instructions: README.md
-- Save your completed copy under practice/duckdb/submissions/

-- Confirm the relevant tables exist.
DESCRIBE ex01_support_tickets;


-- -----------------------------------------------------------------
-- Q1. Return `ticket_id`, `customer_name`, and `status` for every ticket.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q2. Return all tickets whose status is `Open`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q3. Return open or pending tickets with `High` or `Urgent` priority.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q4. Return tickets created after June 15, 2026.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q5. Return closed tickets ordered from longest to shortest `resolution_hours`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q6. Return the five highest satisfaction scores among closed tickets; break ties by newest `created_at`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q7. Return open Billing tickets ordered from oldest to newest.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------
