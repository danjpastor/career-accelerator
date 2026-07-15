-- DuckDB Exercise 11: Explain joins and window functions
-- Source instructions: README.md
-- Save your completed copy under practice/duckdb/submissions/

-- Confirm the relevant tables exist.
DESCRIBE ex11_customer_accounts;
DESCRIBE ex11_support_agents;
DESCRIBE ex11_tickets;


-- -----------------------------------------------------------------
-- Q1. INNER JOIN customer accounts to tickets. Explain which customers disappear and why.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q2. LEFT JOIN customer accounts to tickets. Explain why the row count differs from the INNER JOIN.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q3. Use `ROW_NUMBER` to return the latest ticket for each customer.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q4. Rank agents by average resolution time using `DENSE_RANK`; lower is better.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q5. Calculate each agent's three-ticket rolling average resolution time.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q6. Return customers without tickets.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q7. Write a 3–5 sentence explanation comparing aggregate queries with window-function queries.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------
