# DuckDB Exercise 04: Summarize retail orders

**Week:** 3
**Estimated time:** 40 minutes  
**Concepts:** COUNT, SUM, AVG, GROUP BY, HAVING

## Scenario

A sales manager is preparing a weekly summary of retail orders. The manager needs overall totals, regional performance, channel volume, and discount patterns.

## Tables

- `ex02_retail_orders`

## Source CSV files

- `retail_orders.csv`

## Tasks

### Task 1

Count the orders in the sales file. Return the count as `orders`.

**Result requirements**

- Return columns in this order: `orders`.
- Return 1 row.

### Task 2

Calculate the revenue recorded across all orders. Return it as `revenue`.

**Result requirements**

- Return columns in this order: `revenue`.
- Return 1 row.

### Task 3

The sales manager needs one average order value for the weekly summary. Calculate the average of `revenue`, round it to two decimal places, and name it `average_revenue`.

**Result requirements**

- Return columns in this order: `average_revenue`.
- Return 1 row.
- Round the requested result to 2 decimal places.

### Task 4

Show order volume and revenue for each region. Return `region`, the order count as `orders`, and total revenue as `revenue`.

**Result requirements**

- Return columns in this order: `region`, `orders`, `revenue`.
- Return 4 rows.

### Task 5

Find sales channels that handled more than five orders. Return `sales_channel` and the order count as `orders`.

**Result requirements**

- Return columns in this order: `sales_channel`, `orders`.
- Return 2 rows.

### Task 6

Compare typical discount levels across product categories. Calculate the average `discount_pct` for each `product_category`, round it to two decimal places, and name it `average_discount`.

**Result requirements**

- Return columns in this order: `product_category`, `average_discount`.
- Return 4 rows.
- Round the requested result to 2 decimal places.

### Task 7

Find the region that generated the most revenue. Return `region` and total `revenue`.

**Result requirements**

- Return columns in this order: `region`, `revenue`.
- Return 1 row.

## Complete the exercise

1. Complete each task in the SQL editor.
2. Use **Check Task** for specific feedback and hints.
3. Use **Check Exercise** after every task passes.
4. Select **Submit Exercise** to record completion.

