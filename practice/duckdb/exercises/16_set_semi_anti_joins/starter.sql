-- DuckDB Exercise 12: Compare customer populations with set and existence logic
-- Source instructions: README.md
-- Save your completed work through Career Accelerator.

DESCRIBE ex16_previous_customers;
DESCRIBE ex16_current_customers;
DESCRIBE ex16_orders;

-- -----------------------------------------------------------------
-- Q1. Combine the previous and current customer IDs with UNION.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q2. Combine both customer tables with UNION ALL and count all rows.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q3. Find customers present in both periods with INTERSECT.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q4. Find customers that are new in the current period with EXCEPT.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q5. Return current customers that have at least one order using a semi-join pattern.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q6. Return current customers with no orders using an anti-join pattern.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q7. Explain when UNION ALL is safer than UNION for audit work.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


