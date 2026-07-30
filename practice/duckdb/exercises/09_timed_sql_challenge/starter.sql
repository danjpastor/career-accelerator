-- DuckDB Exercise 31: Complete a timed product analysis
-- Source instructions: README.md
-- Save your completed copy under practice/duckdb/submissions/

-- Confirm the relevant tables exist.
DESCRIBE ex09_users;
DESCRIBE ex09_events;
DESCRIBE ex09_purchases;


-- -----------------------------------------------------------------
-- Q1. Task: Count users by acquisition channel. Required output: return only these columns in this order: `acquisition_channel`, `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 4 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q2. Task: Calculate June purchasers and purchaser conversion rate. Required output: return only these columns in this order: `count(DISTINCT p.user_id)`, `round(((100.0 * count(DISTINCT p.user_id)) / (SELECT count_star() FROM ex09_users)), 2)`. Use these exact names for calculated or summarized columns: `count(DISTINCT p.user_id)`, `round(((100.0 * count(DISTINCT p.user_id)) / (SELECT count_star() FROM ex09_users)), 2)`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q3. Task: Return users with at least three events. Required output: return only these columns in this order: `user_id`. A correct result contains 6 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q4. Task: Calculate revenue by acquisition channel. Required output: return only these columns in this order: `acquisition_channel`, `sum(p.amount)`. Use these exact names for calculated or summarized columns: `sum(p.amount)`. A correct result contains 3 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q5. Task: Use a CTE to return each user's first event date and days from signup to first event. Required output: return only these columns in this order: `count_star()`, `round(avg(date_diff('day', u.signup_date, f.first_event_date)), 2)`. Use these exact names for calculated or summarized columns: `count_star()`, `round(avg(date_diff('day', u.signup_date, f.first_event_date)), 2)`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------
