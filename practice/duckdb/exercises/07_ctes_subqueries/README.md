# DuckDB Exercise 12: Analyze order profitability

**Week:** 4
**Estimated time:** 50 minutes  
**Concepts:** subqueries, CTEs, layered analysis

## Scenario

A merchandising analyst needs order-level revenue, cost, and profit calculations before identifying high-value orders, products, and regions.

## Tables

- `ex07_products`
- `ex07_orders`
- `ex07_order_items`

## Source CSV files

- `order_items.csv`
- `orders.csv`
- `products.csv`

## Tasks

### Task 1

Use a CTE to calculate revenue for every order, then return the number of orders as `order_count` and total revenue rounded to two decimal places as `total_revenue`.

**Result requirements**

- Return columns in this order: `order_count`, `total_revenue`.
- Return 1 row.
- Round the requested result to 2 decimal places.

### Task 2

Use a subquery to return orders whose revenue is above the average order revenue.

**Result requirements**

- Return columns in this order: `order_id`.
- Return 5 rows.

### Task 3

Use a CTE to calculate revenue, cost, and profit for every order. Return the number of orders as `order_count` and total profit rounded to two decimal places as `total_profit`.

**Result requirements**

- Return columns in this order: `order_count`, `total_profit`.
- Return 1 row.
- Round the requested result to 2 decimal places.

### Task 4

Compare revenue and profit by product category. Return `category`, total revenue rounded to two decimal places as `revenue`, and total profit rounded to two decimal places as `profit`.

**Result requirements**

- Return columns in this order: `category`, `revenue`, `profit`.
- Return 4 rows.
- Round the requested result to 2 decimal places.

### Task 5

Return the three products with the highest total profit.

**Result requirements**

- Return columns in this order: `product_name`, `profit`.
- Return 3 rows.

### Task 6

Use one CTE for order profitability and a second CTE for regional summaries. Return each `region` and its total `profit` rounded to two decimal places.

**Result requirements**

- Return columns in this order: `region`, `profit`.
- Return 4 rows.
- Round the requested result to 2 decimal places.

### Task 7

Return regions whose total profit is above the average regional profit.

**Result requirements**

- Return columns in this order: `region`.
- Return 2 rows.

## Complete the exercise

1. Complete each task in the SQL editor.
2. Use **Check Task** for specific feedback and hints.
3. Use **Check Exercise** after every task passes.
4. Select **Submit Exercise** to record completion.

