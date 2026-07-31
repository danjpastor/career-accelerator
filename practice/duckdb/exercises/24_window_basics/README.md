# DuckDB Exercise 14: Add row-level context with window functions

**Week:** 4
**Estimated time:** 45 minutes
**Concepts:** OVER, PARTITION BY, window aggregates, row-level context

## Purpose

Practice the SQL concepts introduced in the matching DataCamp chapter. Complete the work in your own SQL rather than copying a finished query.

## Available tables

- `ex02_retail_orders`

## Scenario

A regional sales manager wants each individual order to remain visible while comparing it with company-wide and regional benchmarks.

## Tasks

### Task 1

Return every order with the overall average revenue added as a window value.

**Result requirements**

- Return columns in this order: `order_id`, `revenue`, `overall_average_revenue`.
- Return 24 rows.

### Task 2

Return every order with the average revenue for its region.

**Result requirements**

- Return columns in this order: `order_id`, `region`, `revenue`, `regional_average_revenue`.
- Return 24 rows.

### Task 3

Return each order with its region total while preserving one row per order.

**Result requirements**

- Return columns in this order: `order_id`, `region`, `revenue`, `regional_revenue`.
- Return 24 rows.

### Task 4

Return each order with its percentage contribution to regional revenue.

**Result requirements**

- Return columns in this order: `order_id`, `region`, `revenue`, `regional_share`.
- Return 24 rows.

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
