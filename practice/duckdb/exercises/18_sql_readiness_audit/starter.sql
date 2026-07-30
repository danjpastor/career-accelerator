-- DuckDB Exercise 33: Complete the final relational data-quality audit
-- Source instructions: README.md
-- Save your completed work through Career Accelerator.

DESCRIBE ex18_customers;
DESCRIBE ex18_orders;
DESCRIBE ex18_payments;

-- -----------------------------------------------------------------
-- Q1. Task: Document the grain and expected key for each table in SQL comments. Required output: return only these columns in this order: `table_name`, `row_count`. Use these exact names for calculated or summarized columns: `table_name`, `row_count`. A correct result contains 3 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q2. Task: Find duplicate order IDs and report their duplicate count. Required output: return only these columns in this order: `order_id`, `row_count`. Use these exact names for calculated or summarized columns: `row_count`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q3. Task: Find orders whose customer_id does not exist in customers. Required output: return only these columns in this order: `order_id`, `customer_id`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q4. Task: Find payments whose order_id does not exist in orders. Required output: return only these columns in this order: `payment_id`, `order_id`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q5. Task: Find required order fields that are NULL or blank. Required output: return only these columns in this order: `order_id`, `issue`. Use these exact names for calculated or summarized columns: `issue`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q6. Task: Reconcile order totals to payment amounts at one row per order and flag differences. Required output: return only these columns in this order: `order_id`, `difference`. Use these exact names for calculated or summarized columns: `difference`. A correct result contains 2 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q7. Task: Build one CTE-based quality summary with issue_type and issue_count. Required output: return only these columns in this order: `issue_type`, `issue_count`. Use these exact names for calculated or summarized columns: `issue_type`, `issue_count`. A correct result contains 5 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q8. Task: Write a three-sentence findings comment naming the highest-risk issue and the next action. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


