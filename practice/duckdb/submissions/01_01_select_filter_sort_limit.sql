-- DuckDB Exercise 01: Filter and sort support tickets
-- Source instructions: README.md
-- Save your completed copy under practice/duckdb/submissions/

-- Confirm the relevant tables exist.
DESCRIBE ex01_support_tickets;


-- -----------------------------------------------------------------

-- Q1. Return `ticket_id`, `customer_name`, and `status` for every ticket.

-- SELECT ticket_id, customer_name, status
-- FROM './practice\duckdb\datasets\01_select_filter_sort_limit\support_tickets.csv'

-- -----------------------------------------------------------------

-- Q2. Return all tickets whose status is `Open`.

-- SELECT *
-- FROM './practice\duckdb\datasets\01_select_filter_sort_limit\support_tickets.csv'
-- WHERE status = 'Open'

-- -----------------------------------------------------------------

-- Q3. Return open or pending tickets with `High` or `Urgent` priority.

-- SELECT *
-- FROM './practice\duckdb\datasets\01_select_filter_sort_limit\support_tickets.csv'
-- WHERE status IN ('Open','Pending') AND priority IN ('Urgent', 'High')

-- -----------------------------------------------------------------

-- Q4. Return tickets created after June 15, 2026.

-- SELECT *
-- FROM './practice\duckdb\datasets\01_select_filter_sort_limit\support_tickets.csv'
-- WHERE created_at >= '2026-06-16';

-- -----------------------------------------------------------------

-- Q5. Return closed tickets ordered from longest to shortest `resolution_hours`.

-- SELECT *
-- FROM './practice\duckdb\datasets\01_select_filter_sort_limit\support_tickets.csv'
-- ORDER BY resolution_hours DESC

-- -----------------------------------------------------------------

-- Q6. Return the five highest satisfaction scores among closed tickets; break ties by newest `created_at`.

-- SELECT *
-- FROM './practice\duckdb\datasets\01_select_filter_sort_limit\support_tickets.csv'
-- WHERE status = 'Closed'
-- ORDER BY satisfaction_score DESC, created_at
-- LIMIT 5;

-- -----------------------------------------------------------------

-- Q7. Return open Billing tickets ordered from oldest to newest.

-- SELECT *
-- FROM './practice\duckdb\datasets\01_select_filter_sort_limit\support_tickets.csv'
-- WHERE category = 'Billing' AND status = 'Open'
-- ORDER BY created_at

-- -----------------------------------------------------------------
