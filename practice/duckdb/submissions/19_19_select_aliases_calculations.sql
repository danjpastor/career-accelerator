-- DuckDB Exercise 02: Prepare a retail order review
-- Read README.md before starting.
-- Save your completed copy under practice/duckdb/submissions/


-- -----------------------------------------------------------------

-- Q1. Check what each order would be worth before discounts. Return `order_id`, `quantity`, `unit_price`, and `quantity * unit_price` as `line_value`.

SELECT order_id,
    quantity,
    unit_price,
    (quantity*unit_price) AS line_value
FROM ex02_retail_orders;

-- -----------------------------------------------------------------

-- Q2. Prepare a sales report with consistent headings. Return `order_id`; rename `region` to `sales_region`, `sales_channel` to `channel`, and `revenue` to `recorded_revenue`.

SELECT
    order_id,
    region AS sales_region,
    sales_channel AS channel,
    revenue AS recorded_revenue
FROM ex02_retail_orders;

-- -----------------------------------------------------------------

-- Q3. Check whether the revenue stored for each order matches quantity multiplied by unit price. Return `order_id`, rename `revenue` to `recorded_revenue`, and calculate the difference as `revenue_difference`.

SELECT
    order_id,
    revenue AS recorded_revenue,
    quantity*unit_price AS revenue_difference
FROM ex02_retail_orders;

-- -----------------------------------------------------------------

-- Q4. List every region and sales-channel combination used by the business. Return unique `region` and `sales_channel` pairs, sorted by region and then sales channel.

SELECT
    DISTINCT region,
    sales_channel
FROM ex02_retail_orders
ORDER BY region, sales_channel;

-- -----------------------------------------------------------------
