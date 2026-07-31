-- DuckDB Exercise 03: Filter support and feedback records
-- Read README.md before starting.
-- Save your completed copy under practice/duckdb/submissions/


-- -----------------------------------------------------------------

-- Q1. List the ticket statuses currently used by the support team. Return each unique `status` in alphabetical order.

SELECT
    DISTINCT status
FROM ex01_support_tickets
ORDER BY status

-- -----------------------------------------------------------------

-- Q2. Find high-priority tickets that are still active. Return `ticket_id`, `priority`, and `status` for High or Urgent tickets that are not Closed.

SELECT
    ticket_id,
    priority,
    status
FROM ex01_support_tickets
WHERE priority IN ('High', 'Urgent') AND status != 'Closed';

-- -----------------------------------------------------------------

-- Q3. Find tickets that do not have a recorded resolution time. Return `ticket_id`, `status`, and `resolution_hours`.

SELECT
    ticket_id,
    status,
    resolution_hours
FROM ex01_support_tickets
WHERE resolution_hours IS NULL;

-- -----------------------------------------------------------------

-- Q4. Find feedback submitted through email, even when the channel text uses different capitalization or extra spaces. Return `response_id` and `channel_raw`.

SELECT response_id, LOWER(TRIM(channel_raw)) AS channel_raw
FROM ex03_customer_feedback_dirty
WHERE LOWER(TRIM(channel_raw)) = 'email';

-- -----------------------------------------------------------------
