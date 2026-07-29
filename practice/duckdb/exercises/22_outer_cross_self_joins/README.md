# DuckDB Exercise 22: Compare outer, cross, and self joins

**Week:** 4
**Estimated time:** 45 minutes
**Concepts:** LEFT JOIN, FULL JOIN, CROSS JOIN, SELF JOIN

## Purpose

Practice the SQL concepts introduced in the matching DataCamp chapter. Complete the work in your own SQL rather than copying a finished query.

## Available tables

- `ex06_customers`
- `ex06_orders`
- `ex10_employees`
- `ex10_departments`

## Questions

1. Use a left join to show every customer and any related orders, keeping customers with no order.
2. Use a full join to identify customer IDs that appear on only one side of the customer-order relationship.
3. Use a self join to show each employee beside their manager name when one exists.
4. Use a cross join to build every combination of department and two named planning scenarios.

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
