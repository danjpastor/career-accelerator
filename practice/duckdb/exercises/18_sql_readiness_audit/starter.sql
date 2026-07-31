-- DuckDB Exercise 33: Complete a full relational data-quality audit
-- Source instructions: README.md
-- Save your completed work through Career Accelerator.

DESCRIBE ex18_customers;
DESCRIBE ex18_orders;
DESCRIBE ex18_payments;

-- -----------------------------------------------------------------
-- Q1. Document the grain and expected key for each table in SQL comments.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q2. Find duplicate order IDs and report their duplicate count.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q3. Find orders whose customer_id does not exist in customers.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q4. Find payments whose order_id does not exist in orders.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q5. Find required order fields that are NULL or blank.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q6. Reconcile order totals to payment amounts at one row per order and flag differences.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q7. Build one CTE-based quality summary with issue_type and issue_count.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q8. Write a three-sentence SQL comment naming the highest-risk data issue and the next action, then return the total audit row count as `audit_rows`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


