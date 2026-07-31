# DuckDB Exercise 10: Use subqueries in filters, sources, and calculations

**Week:** 4
**Estimated time:** 45 minutes
**Concepts:** subqueries in WHERE, FROM, and SELECT

## Purpose

Practice the SQL concepts introduced in the matching DataCamp chapter. Complete the work in your own SQL rather than copying a finished query.

## Available tables

- `ex02_retail_orders`
- `ex07_orders`
- `ex07_order_items`
- `ex07_products`

## Scenario

A retail analyst is investigating above-average orders, order-item revenue, and products that have actually sold. Different parts of the report call for subqueries in different locations.

## Tasks

### Task 1

Use a subquery in WHERE to return retail orders whose revenue is above the overall average.

**Result requirements**

- Return columns in this order: `order_id`, `region`, `revenue`.
- Return 9 rows.

### Task 2

Use a subquery in FROM to calculate total item revenue per order and then return the summarized rows.

**Result requirements**

- Return columns in this order: `order_id`, `order_revenue`.
- Return 10 rows.

### Task 3

Use a scalar subquery in SELECT to show each retail order revenue beside the overall average revenue.

**Result requirements**

- Return columns in this order: `order_id`, `revenue`, `overall_average_revenue`.
- Return 24 rows.

### Task 4

Use a nested or correlated subquery to return products that appear in at least one order item.

**Result requirements**

- Return columns in this order: `product_id`, `product_name`.
- Return 8 rows.

## Complete the exercise

1. Complete each task in the SQL editor.
2. Use **Check Task** for specific feedback and hints.
3. Use **Check Exercise** after every task passes.
4. Select **Submit Exercise** to record completion.

## Common mistakes

- Using a concept before its prerequisite chapter is complete.
- Returning the right number of rows with the wrong grain.
- Leaving columns unqualified when more than one table contains the same name.
- Typing expected results instead of deriving them from the data.
