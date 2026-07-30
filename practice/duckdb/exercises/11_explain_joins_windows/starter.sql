-- DuckDB Exercise 18: Explain join and window-function results
-- Source instructions: README.md
-- Save your completed copy under practice/duckdb/submissions/

-- Confirm the relevant tables exist.
DESCRIBE ex11_customer_accounts;
DESCRIBE ex11_support_agents;
DESCRIBE ex11_tickets;


-- -----------------------------------------------------------------
-- Q1. Task: INNER JOIN customer accounts to tickets. Explain which customers disappear and why. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q2. Task: LEFT JOIN customer accounts to tickets. Explain why the row count differs from the INNER JOIN. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q3. Task: Use `ROW_NUMBER` to return the latest ticket for each customer. Required output: return only these columns in this order: `customer_id`, `ticket_id`. A correct result contains 7 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q4. Task: Rank agents by average resolution time using `DENSE_RANK`; lower is better. Required output: return only these columns in this order: `agent_id`, `avg_hours`, `performance_rank`. Use these exact names for calculated or summarized columns: `avg_hours`, `performance_rank`. A correct result contains 6 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q5. Task: Calculate each agent's three-ticket rolling average resolution time. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q6. Task: Return customers without tickets. Required output: return only these columns in this order: `customer_id`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q7. Task: Write a 3–5 sentence explanation comparing aggregate queries with window-function queries. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------
