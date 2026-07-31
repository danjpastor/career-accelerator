-- DuckDB Exercise 18: Explain joins and window functions
-- Source instructions: README.md
-- Save your completed copy under practice/duckdb/submissions/

-- Confirm the relevant tables exist.
DESCRIBE ex11_customer_accounts;
DESCRIBE ex11_support_agents;
DESCRIBE ex11_tickets;


-- -----------------------------------------------------------------
-- Q1. Use an inner join between customer accounts and tickets. Return the joined row count as `inner_join_rows` and add a SQL comment explaining which customers disappear and why.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q2. Use a left join between customer accounts and tickets. Return the joined row count as `left_join_rows` and add a SQL comment explaining why it differs from the inner join.
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
-- Q5. Calculate each agent’s trailing three-ticket average resolution time, then return the number of result rows as `rolling_average_rows`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q6. Return customers without tickets.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q7. Write a 3–5 sentence SQL comment comparing aggregate queries with window-function queries, then return the ticket row count as `comparison_rows`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------
