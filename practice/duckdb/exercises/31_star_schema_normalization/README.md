# DuckDB Exercise 31: Reshape operational data into analytical tables

**Week:** 6
**Estimated time:** 50 minutes
**Concepts:** fact tables, dimensions, normalization, star-schema joins

## Purpose

Practice the SQL concepts introduced in the matching DataCamp chapter. Complete the work in your own SQL rather than copying a finished query.

## Available tables

- `ex06_customers`
- `ex06_orders`
- `ex06_payments`

## Questions

1. Return a customer dimension-style result with one row per customer.
2. Return an order fact-style result with order measures and customer key.
3. Join the proposed fact and dimension outputs to summarize revenue by region.
4. Validate that the dimension key remains unique and report any duplicates.

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
