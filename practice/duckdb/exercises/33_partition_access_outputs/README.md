# DuckDB Exercise 29: Plan partitioning and access-safe outputs

**Week:** 7
**Estimated time:** 45 minutes
**Concepts:** partition-key analysis, restricted projections, database management reasoning

## Purpose

Practice the SQL concepts introduced in the matching DataCamp chapter. Complete the work in your own SQL rather than copying a finished query.

## Available tables

- `ex06_customers`
- `ex06_orders`

## Questions

1. Task: Summarize order volume by month to evaluate a possible date partition key. Required output: return only these columns in this order: `order_month`, `order_count`. Do not include extra columns; keep every filter and sort rule stated in the task.
2. Task: Summarize order volume by region to evaluate whether region would create balanced partitions. Required output: return only these columns in this order: `region`, `order_count`. Do not include extra columns; keep every filter and sort rule stated in the task.
3. Task: Create a restricted customer output that excludes signup date while retaining the analytical key and region. Required output: return only these columns in this order: `customer_id`, `customer_name`, `region`. A correct result contains 10 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
4. Task: Create a restricted order output that exposes order status and total without customer names. Required output: return only these columns in this order: `order_id`, `customer_id`, `order_total`, `order_status`. A correct result contains 14 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
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
