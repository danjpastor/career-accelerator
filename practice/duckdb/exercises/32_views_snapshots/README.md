# DuckDB Exercise 28: Create reusable views and analytical snapshots

**Week:** 6
**Estimated time:** 45 minutes
**Concepts:** views, reusable logic, snapshot tables, refresh validation

## Purpose

Practice the SQL concepts introduced in the matching DataCamp chapter. Complete the work in your own SQL rather than copying a finished query.

## Available tables

- `ex06_customers`
- `ex06_orders`

## Scenario

An analytics team wants a reusable delivered-orders view and a temporary snapshot that can be checked before a reporting workflow is published.

## Tasks

### Task 1

Create a temporary view that joins delivered orders to customer region, then return `order_id`, `customer_id`, `region`, and `order_total` from the view.

**Result requirements**

- Return columns in this order: `order_id`, `customer_id`, `region`, `order_total`.
- Return 12 rows.

### Task 2

Create the temporary delivered-orders view in this task, then summarize its revenue by region. Return `region` and `delivered_revenue`.

**Result requirements**

- Return columns in this order: `region`, `delivered_revenue`.

### Task 3

Create the temporary delivered-orders view and a temporary snapshot table from it, then return the snapshot row count as `snapshot_rows`.

**Result requirements**

- Return columns in this order: `snapshot_rows`.
- Return 1 row.

### Task 4

Create the temporary delivered-orders view and snapshot table in this task. Return `view_rows`, `snapshot_rows`, and their `difference` to confirm they match.

**Result requirements**

- Return columns in this order: `view_rows`, `snapshot_rows`, `difference`.
- Return 1 row.

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
