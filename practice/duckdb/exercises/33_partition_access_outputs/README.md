# DuckDB Exercise 29: Plan partitioning and access-safe outputs

**Week:** 7
**Estimated time:** 45 minutes
**Concepts:** partition-key analysis, restricted projections, database management reasoning

## Purpose

Practice the SQL concepts introduced in the matching DataCamp chapter. Complete the work in your own SQL rather than copying a finished query.

## Available tables

- `ex06_customers`
- `ex06_orders`

## Tasks

### Task 1

Summarize order volume by month to evaluate a possible date partition key.

**Result requirements**

- **Return columns:** `order_month`, `order_count`

### Task 2

Summarize order volume by region to evaluate whether region would create balanced partitions.

**Result requirements**

- **Return columns:** `region`, `order_count`

### Task 3

Create a restricted customer output that excludes signup date while retaining the analytical key and region.

**Result requirements**

- **Return columns:** `customer_id`, `customer_name`, `region`
- **Expected rows:** 10

### Task 4

Create a restricted order output that exposes order status and total without customer names.

**Result requirements**

- **Return columns:** `order_id`, `customer_id`, `order_total`, `order_status`
- **Expected rows:** 14
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
