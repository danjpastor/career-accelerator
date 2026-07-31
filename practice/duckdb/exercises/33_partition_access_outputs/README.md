# DuckDB Exercise 29: Plan partitioning and access-safe outputs

**Week:** 6
**Estimated time:** 45 minutes
**Concepts:** partition-key analysis, restricted projections, database management reasoning

## Purpose

Practice the SQL concepts introduced in the matching DataCamp chapter. Complete the work in your own SQL rather than copying a finished query.

## Available tables

- `ex06_customers`
- `ex06_orders`

## Scenario

A data platform analyst is evaluating partition choices and preparing restricted outputs that expose useful fields without unnecessary sensitive details.

## Tasks

### Task 1

Summarize order volume by month to evaluate a possible date partition key.

**Result requirements**

- Return columns in this order: `order_month`, `order_count`.

### Task 2

Summarize order volume by region to evaluate whether region would create balanced partitions.

**Result requirements**

- Return columns in this order: `region`, `order_count`.

### Task 3

Create a restricted customer output that excludes signup date while retaining the analytical key and region.

**Result requirements**

- Return columns in this order: `customer_id`, `customer_name`, `region`.
- Return 10 rows.

### Task 4

Create a restricted order output that exposes order status and total without customer names.

**Result requirements**

- Return columns in this order: `order_id`, `customer_id`, `order_total`, `order_status`.
- Return 14 rows.

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
