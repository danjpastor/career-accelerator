# DuckDB Exercise 05: Join orders to customers

**Week:** 4
**Estimated time:** 40 minutes
**Concepts:** INNER JOIN, join keys, qualified columns, joined filters

## Purpose

Practice the SQL concepts introduced in the matching DataCamp chapter. Complete the work in your own SQL rather than copying a finished query.

## Available tables

- `ex06_customers`
- `ex06_orders`
- `ex06_payments`

## Questions

1. Task: Join orders to customers and return one row per matched order with customer name and region. Required output: return only these columns in this order: `order_id`, `customer_name`, `region`, `order_total`. A correct result contains 14 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
2. Task: Return only delivered orders after joining orders to customers. Required output: return only these columns in this order: `order_id`, `customer_name`, `order_status`. A correct result contains 12 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
3. Task: Join payments to orders and return the payment amount beside the order total. Required output: return only these columns in this order: `payment_id`, `order_id`, `amount`, `order_total`. A correct result contains 12 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
4. Task: Summarize matched order revenue by customer region. Required output: return only these columns in this order: `region`, `order_count`, `order_revenue`. A correct result contains 4 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
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
