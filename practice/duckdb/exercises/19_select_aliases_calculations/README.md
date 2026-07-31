# DuckDB Exercise 02: Build clear selected fields and calculated columns

**Week:** 3
**Estimated time:** 35 minutes
**Concepts:** column selection, aliases, arithmetic expressions, DISTINCT

## Purpose

Practice the SQL concepts introduced in the matching DataCamp chapter. Complete the work in your own SQL rather than copying a finished query.

## Available tables

- `ex02_retail_orders`

## Scenario

A retail operations manager is preparing order data for a shared sales report. The manager needs useful calculated fields, consistent headings, and a check against recorded revenue.

## Tasks

### Task 1

The merchandising team wants to calculate the expected value of each order from its quantity and unit price. Return `order_id`, `quantity`, `unit_price`, and calculate `quantity * unit_price` as `line_value`.

**Result requirements**

- Return columns in this order: `order_id`, `quantity`, `unit_price`, `line_value`.
- Return 24 rows.

### Task 2

The sales manager wants consistent column headings in a shared order report. Return `order_id`; rename `region` to `sales_region`, `sales_channel` to `channel`, and `revenue` to `recorded_revenue`.

**Result requirements**

- Return columns in this order: `order_id`, `sales_region`, `channel`, `recorded_revenue`.
- Return 24 rows.

### Task 3

Check whether the revenue stored for each order matches quantity multiplied by unit price. Return `order_id`, rename `revenue` to `recorded_revenue`, and calculate the difference as `revenue_difference`.

**Result requirements**

- Return columns in this order: `order_id`, `recorded_revenue`, `revenue_difference`.
- Return 24 rows.

### Task 4

List every region and sales-channel combination used by the business. Return unique `region` and `sales_channel` pairs, sorted by region and then sales channel.

**Result requirements**

- Return columns in this order: `region`, `sales_channel`.
- Return 12 rows.

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
