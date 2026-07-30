-- DuckDB Exercise 12: Analyze order profitability with subqueries and CTEs
-- Source instructions: README.md
-- Save your completed copy under practice/duckdb/submissions/

-- Confirm the relevant tables exist.
DESCRIBE ex07_products;
DESCRIBE ex07_orders;
DESCRIBE ex07_order_items;


-- -----------------------------------------------------------------
-- Q1. Task: Use a CTE to calculate revenue for every order. Required output: return only these columns in this order: `count_star()`, `round(sum(revenue), 2)`. Use these exact names for calculated or summarized columns: `count_star()`, `round(sum(revenue), 2)`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q2. Task: Use a subquery to return orders whose revenue is above the average order revenue. Required output: return only these columns in this order: `order_id`. A correct result contains 5 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q3. Task: Use a CTE to calculate revenue, cost, and profit by order. Required output: return only these columns in this order: `count_star()`, `round(sum(profit), 2)`. Use these exact names for calculated or summarized columns: `count_star()`, `round(sum(profit), 2)`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q4. Task: Calculate revenue and profit by product category. Required output: return only these columns in this order: `category`, `round(sum((i.quantity * i.sale_price)), 2)`, `round(sum((i.quantity * (i.sale_price - p.unit_cost))), 2)`. Use these exact names for calculated or summarized columns: `round(sum((i.quantity * i.sale_price)), 2)`, `round(sum((i.quantity * (i.sale_price - p.unit_cost))), 2)`. A correct result contains 4 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q5. Task: Return the three products with the highest total profit. Required output: return only these columns in this order: `product_name`, `profit`. Use these exact names for calculated or summarized columns: `profit`. A correct result contains 3 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q6. Task: Create two CTEs: one for order profitability and one for regional summaries. Required output: return only these columns in this order: `region`, `round(profit, 2)`. Use these exact names for calculated or summarized columns: `round(profit, 2)`. A correct result contains 4 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q7. Task: Return regions whose total profit is above the average regional profit. Required output: return only these columns in this order: `region`. A correct result contains 2 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------
