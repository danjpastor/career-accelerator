-- DuckDB Exercise 01: Filter and sort support tickets
-- Source instructions: README.md
-- Save your completed copy under practice/duckdb/submissions/

-- Confirm the relevant tables exist.


-- -----------------------------------------------------------------
-- Q1. Return `ticket_id`, `customer_name`, and `status` for every ticket.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------
-- SELECT ticket_id, customer_name, status
-- FROM './practice\duckdb\datasets\01_select_filter_sort_limit\support_tickets.csv' 

-- -----------------------------------------------------------------
-- Q2. Return all tickets whose status is `Open`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------
-- SELECT *
-- FROM './practice\duckdb\datasets\01_select_filter_sort_limit\support_tickets.csv'
-- WHERE status = 'Open'

-- -----------------------------------------------------------------
-- Q3. Return open or pending tickets with `High` or `Urgent` priority.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------
SELECT *
FROM './practice\duckdb\datasets\01_select_filter_sort_limit\support_tickets.csv'
WHERE (status = 'Open' OR status = 'Pending')
    AND priority = 'High' OR priority = 'Urgent';

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
