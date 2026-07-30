# DuckDB Exercise 19: Build subtotal and pivot-style summaries

**Week:** 5
**Estimated time:** 50 minutes
**Concepts:** ROLLUP, CUBE, GROUPING SETS, FILTER-based pivots

## Purpose

Practice the SQL concepts introduced in the matching DataCamp chapter. Complete the work in your own SQL rather than copying a finished query.

## Available tables

- `ex02_retail_orders`

## Questions

1. Task: Create region and product-category subtotals using ROLLUP. Required output: return only these columns in this order: `region`, `product_category`, `revenue`. Do not include extra columns; keep every filter and sort rule stated in the task.
2. Task: Create combinations of region and sales channel using CUBE. Required output: return only these columns in this order: `region`, `sales_channel`, `revenue`. Do not include extra columns; keep every filter and sort rule stated in the task.
3. Task: Build a pivot-style summary with one row per region and separate revenue columns for Online and Store. Required output: return only these columns in this order: `region`, `online_revenue`, `store_revenue`. A correct result contains 4 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
4. Task: Use GROUPING SETS to return region totals, channel totals, and an overall total in one result. Required output: return only these columns in this order: `region`, `sales_channel`, `revenue`. Do not include extra columns; keep every filter and sort rule stated in the task.
## Completion evidence

1. Copy `starter.sql` to the DuckDB submissions folder.
2. Answer every question with your own SQL.
3. Use **Check Answer** only after you have attempted the query.
4. Add a short comment describing one mistake you corrected or validation decision you made.
5. Mark the exercise complete only after every checkpoint passes.

## Common mistakes

- Using a concept before its prerequisite chapter is complete.
- Returning the right number of rows with the wrong grain.
- Leaving columns unqualified when more than one table contains the same name.
- Typing expected results instead of deriving them from the data.
