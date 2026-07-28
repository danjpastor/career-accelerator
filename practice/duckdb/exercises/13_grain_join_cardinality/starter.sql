-- DuckDB Exercise 13: Audit table grain and join cardinality
-- Source instructions: README.md
-- Save your completed work through Career Accelerator.

DESCRIBE ex13_accounts;
DESCRIBE ex13_orders;
DESCRIBE ex13_contacts;

-- -----------------------------------------------------------------
-- Q1. Profile the row count and distinct business key count for each table.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q2. Find account IDs that appear more than once in the contacts table.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q3. Join orders directly to contacts and compare the resulting row count with the original order count.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q4. Calculate the multiplication factor created by the direct join.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q5. Pre-aggregate contacts to one row per account, then join that result to orders without changing the order grain.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q6. Find accounts with no orders.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q7. Write a short SQL comment stating the grain of the safe final result.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


