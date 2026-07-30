# DuckDB Exercise 28: Create reusable views and analytical snapshots

**Week:** 6
**Estimated time:** 45 minutes
**Concepts:** views, reusable logic, snapshot tables, refresh validation

## Purpose

Practice the SQL concepts introduced in the matching DataCamp chapter. Complete the work in your own SQL rather than copying a finished query.

## Available tables

- `ex06_customers`
- `ex06_orders`

## Questions

1. Task: Create a reusable view that joins delivered orders to customer region, then return the view rows. Required output: return only these columns in this order: `order_id`, `customer_id`, `region`, `order_total`. A correct result contains 12 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
2. Task: Query the reusable view to summarize delivered revenue by region. Required output: return only these columns in this order: `region`, `delivered_revenue`. Do not include extra columns; keep every filter and sort rule stated in the task.
3. Task: Create a physical snapshot table from the view and return its row count. Required output: return only these columns in this order: `snapshot_rows`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
4. Task: Compare the view and snapshot row counts to verify the snapshot was created correctly. Required output: return only these columns in this order: `view_rows`, `snapshot_rows`, `difference`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
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
