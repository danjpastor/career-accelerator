-- DuckDB Exercise 12: Analyze order profitability
-- Source instructions: README.md
-- Save your completed copy under practice/duckdb/submissions/

-- Confirm the relevant tables exist.
DESCRIBE ex07_products;
DESCRIBE ex07_orders;
DESCRIBE ex07_order_items;


-- -----------------------------------------------------------------
-- Q1. Use a CTE to calculate revenue for every order, then return the number of orders as `order_count` and total revenue rounded to two decimal places as `total_revenue`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q2. Use a subquery to return orders whose revenue is above the average order revenue.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q3. Use a CTE to calculate revenue, cost, and profit for every order. Return the number of orders as `order_count` and total profit rounded to two decimal places as `total_profit`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q4. Compare revenue and profit by product category. Return `category`, total revenue rounded to two decimal places as `revenue`, and total profit rounded to two decimal places as `profit`.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q5. Return the three products with the highest total profit.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q6. Use one CTE for order profitability and a second CTE for regional summaries. Return each `region` and its total `profit` rounded to two decimal places.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------


-- -----------------------------------------------------------------
-- Q7. Return regions whose total profit is above the average regional profit.
-- Write and run your query below this comment.
-- -----------------------------------------------------------------
