-- DuckDB Exercise 31: Timed product challenge
-- Source instructions: README.md
-- Save your completed copy under practice/duckdb/submissions/

-- Confirm the relevant tables exist.
DESCRIBE ex09_users;
DESCRIBE ex09_events;
DESCRIBE ex09_purchases;


-- -----------------------------------------------------------------
-- Q1. Show how many users were acquired through each channel. Return `acquisition_channel` and the count as `user_count`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q2. Count distinct users who made a purchase in June and calculate their share of all users. Return `june_purchasers` and `purchaser_conversion_pct`, rounded to two decimal places.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q3. Return users with at least three events.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q4. Show purchase revenue by acquisition channel. Return `acquisition_channel` and total `revenue`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q5. Use a CTE to find each user’s first event date. Return the number of users as `user_count` and average days from signup to first event, rounded to two decimal places, as `average_days_to_first_event`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------
