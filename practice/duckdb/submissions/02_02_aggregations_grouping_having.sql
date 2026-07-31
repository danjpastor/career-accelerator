-- DuckDB Exercise 04: Summarize retail orders with grouped metrics
-- Source instructions: README.md
-- Save your completed copy under practice/duckdb/submissions/

-- Confirm the relevant tables exist.
DESCRIBE ex02_retail_orders;


-- -----------------------------------------------------------------

-- Q1. Count the orders in the sales file. Return the count as `orders`.

SELECT
    COUNT(order_id) AS orders
FROM ex02_retail_orders;

-- -----------------------------------------------------------------

-- Q2. Calculate the revenue recorded across all orders. Return it as `revenue`.

SELECT
    SUM(revenue) AS revenue
FROM ex02_retail_orders;

-- -----------------------------------------------------------------

-- Q3. The sales manager needs one average order value for the weekly summary. Calculate the average of `revenue`, round it to two decimal places, and name it `average_revenue`.

SELECT
     ROUND(AVG(revenue), 2) AS average_revenue
FROM ex02_retail_orders;

-- -----------------------------------------------------------------

-- Q4. Show order volume and revenue for each region. Return `region`, the order count as `orders`, and total revenue as `revenue`.

SELECT
    DISTINCT region,
    COUNT(*) AS orders,
    SUM(revenue) AS revenue
FROM ex02_retail_orders
GROUP BY region;

-- -----------------------------------------------------------------

-- Q5. Find sales channels that handled more than five orders. Return `sales_channel` and the order count as `orders`.

SELECT
    sales_channel,
    COUNT(*) AS orders
FROM ex02_retail_orders
GROUP BY sales_channel
HAVING COUNT(*) > 5

-- -----------------------------------------------------------------

-- Q6. Compare typical discount levels across product categories. Calculate the average `discount_pct` for each `product_category`, round it to two decimal places, and name it `average_discount`.

SELECT
    product_category,
    ROUND(AVG(discount_pct), 2) AS average_discount
FROM ex02_retail_orders
GROUP BY product_category;

-- -----------------------------------------------------------------

-- Q7. Find the region that generated the most revenue. Return `region` and total `revenue`.

SELECT
    region,
    SUM(revenue) AS revenue
FROM ex02_retail_orders
GROUP BY region
ORDER BY revenue DESC
LIMIT 1;

-- -----------------------------------------------------------------
