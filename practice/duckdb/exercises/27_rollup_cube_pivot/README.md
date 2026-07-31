# DuckDB Exercise 19: Build subtotal and pivot-style summaries

**Week:** 5
**Estimated time:** 50 minutes
**Concepts:** ROLLUP, CUBE, GROUPING SETS, FILTER-based pivots

## Purpose

Practice the SQL concepts introduced in the matching DataCamp chapter. Complete the work in your own SQL rather than copying a finished query.

## Available tables

- `ex02_retail_orders`

## Scenario

Leadership needs one flexible sales summary that can show subtotals, cross-tab comparisons, and an overall total without separate reports.

## Tasks

### Task 1

Create region and product-category subtotals using ROLLUP.

**Result requirements**

- Return columns in this order: `region`, `product_category`, `revenue`.

### Task 2

Create combinations of region and sales channel using CUBE.

**Result requirements**

- Return columns in this order: `region`, `sales_channel`, `revenue`.

### Task 3

Build a pivot-style summary with one row per region and separate revenue columns for Online and Store.

**Result requirements**

- Return columns in this order: `region`, `online_revenue`, `store_revenue`.
- Return 4 rows.

### Task 4

Use GROUPING SETS to return region totals, channel totals, and an overall total in one result.

**Result requirements**

- Return columns in this order: `region`, `sales_channel`, `revenue`.

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
