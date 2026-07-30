# DuckDB Exercise 02: Select, rename, and calculate order fields

**Week:** 3
**Estimated time:** 35 minutes
**Concepts:** column selection, aliases, arithmetic expressions, DISTINCT

## Purpose

Practice the SQL concepts introduced in the matching DataCamp chapter. Complete the work in your own SQL rather than copying a finished query.

## Available tables

- `ex02_retail_orders`

## Questions

1. Task: Return every order with order ID, quantity, unit price, and a calculated pre-discount line value. Required output: return only these columns in this order: `order_id`, `quantity`, `unit_price`, `line_value`. A correct result contains 24 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
2. Task: Return every order with concise aliases for region, channel, and recorded revenue. Required output: return only these columns in this order: `order_id`, `sales_region`, `channel`, `recorded_revenue`. A correct result contains 24 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
3. Task: Return each order with its recorded revenue and the difference between recorded revenue and quantity multiplied by unit price. Required output: return only these columns in this order: `order_id`, `recorded_revenue`, `revenue_difference`. A correct result contains 24 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
4. Task: Return the distinct combinations of region and sales channel, ordered consistently. Required output: return only these columns in this order: `region`, `sales_channel`. A correct result contains 12 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
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
