-- DuckDB Exercise 08: Compare customer groups with set logic
-- Source instructions: README.md
-- Save your completed work through Career Accelerator.

DESCRIBE ex16_previous_customers;
DESCRIBE ex16_current_customers;
DESCRIBE ex16_orders;

-- -----------------------------------------------------------------
-- Q1. Task: Combine the previous and current customer IDs with UNION. Required output: return only these columns in this order: `distinct_customer_count`. Use these exact names for calculated or summarized columns: `distinct_customer_count`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q2. Task: Combine both customer tables with UNION ALL and count all rows. Required output: return only these columns in this order: `all_row_count`. Use these exact names for calculated or summarized columns: `all_row_count`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q3. Task: Find customers present in both periods with INTERSECT. Required output: return only these columns in this order: `customer_id`. A correct result contains 4 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q4. Task: Find customers that are new in the current period with EXCEPT. Required output: return only these columns in this order: `customer_id`. A correct result contains 3 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q5. Task: Return current customers that have at least one order using a semi-join pattern. Required output: return only these columns in this order: `customer_id`. A correct result contains 3 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q6. Task: Return current customers with no orders using an anti-join pattern. Required output: return only these columns in this order: `customer_id`. A correct result contains 3 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q7. Task: Explain when UNION ALL is safer than UNION for audit work. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


