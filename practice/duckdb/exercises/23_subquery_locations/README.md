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

## Questions

1. Task: Use a subquery in WHERE to return retail orders whose revenue is above the overall average. Required output: return only these columns in this order: `order_id`, `region`, `revenue`. A correct result contains 9 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
2. Task: Use a subquery in FROM to calculate total item revenue per order and then return the summarized rows. Required output: return only these columns in this order: `order_id`, `order_revenue`. A correct result contains 10 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
3. Task: Use a scalar subquery in SELECT to show each retail order revenue beside the overall average revenue. Required output: return only these columns in this order: `order_id`, `revenue`, `overall_average_revenue`. A correct result contains 24 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
4. Task: Use a nested or correlated subquery to return products that appear in at least one order item. Required output: return only these columns in this order: `product_id`, `product_name`. A correct result contains 8 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
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
