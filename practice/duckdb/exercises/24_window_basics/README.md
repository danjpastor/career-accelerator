# DuckDB Exercise 15: Add row-level context with window functions

**Week:** 4
**Estimated time:** 45 minutes
**Concepts:** OVER, PARTITION BY, window aggregates, row-level context

## Purpose

Practice the SQL concepts introduced in the matching DataCamp chapter. Complete the work in your own SQL rather than copying a finished query.

## Available tables

- `ex02_retail_orders`

## Questions

1. Return every order with the overall average revenue added as a window value.
2. Return every order with the average revenue for its region.
3. Return each order with its region total while preserving one row per order.
4. Return each order with its percentage contribution to regional revenue.

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
