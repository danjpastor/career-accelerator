-- DuckDB Exercise 01: Filter and sort support tickets
-- Source instructions: README.md
-- Save your completed copy under practice/duckdb/submissions/

-- Confirm the relevant tables exist.
DESCRIBE ex01_support_tickets;


-- -----------------------------------------------------------------
-- Q1. Prepare the manager's basic ticket list. Return `ticket_id`, `customer_name`, and `status` for every ticket.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q2. Find the tickets that are still open. Return only `ticket_id`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q3. Find active tickets that need the fastest attention. Return only `ticket_id` for tickets with High or Urgent priority whose status is Open or Pending.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q4. Find tickets created after June 15, 2026. Return only `ticket_id`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q5. Review how long closed tickets took to resolve. Return `ticket_id` and `resolution_hours`, sorted from longest to shortest.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q6. Show the five closed tickets with the highest satisfaction scores. Return `ticket_id` and `satisfaction_score`; when scores tie, show the newest ticket first.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q7. Find open Billing tickets for follow-up. Return only `ticket_id`, sorted from oldest to newest.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------
