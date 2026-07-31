-- DuckDB Exercise 04: Summarize retail orders
-- Source instructions: README.md
-- Save your completed copy under practice/duckdb/submissions/

-- Confirm the relevant tables exist.
DESCRIBE ex02_retail_orders;


-- -----------------------------------------------------------------
-- Q1. Count the orders in the sales file. Return the count as `orders`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q2. Calculate the revenue recorded across all orders. Return it as `revenue`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q3. The sales manager needs one average order value for the weekly summary. Calculate the average of `revenue`, round it to two decimal places, and name it `average_revenue`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q4. Show order volume and revenue for each region. Return `region`, the order count as `orders`, and total revenue as `revenue`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q5. Find sales channels that handled more than five orders. Return `sales_channel` and the order count as `orders`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q6. Compare typical discount levels across product categories. Calculate the average `discount_pct` for each `product_category`, round it to two decimal places, and name it `average_discount`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q7. Find the region that generated the most revenue. Return `region` and total `revenue`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------
