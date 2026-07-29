# DuckDB Exercise 14: Use subqueries in filters, sources, and calculations

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

1. Use a subquery in WHERE to return retail orders whose revenue is above the overall average.
2. Use a subquery in FROM to calculate total item revenue per order and then return the summarized rows.
3. Use a scalar subquery in SELECT to show each retail order revenue beside the overall average revenue.
4. Use a nested or correlated subquery to return products that appear in at least one order item.

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
