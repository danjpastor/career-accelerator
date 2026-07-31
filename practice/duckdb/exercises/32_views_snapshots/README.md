# DuckDB Exercise 28: Create reusable views and analytical snapshots

**Week:** 6
**Estimated time:** 45 minutes
**Concepts:** views, reusable logic, snapshot tables, refresh validation

## Purpose

Practice the SQL concepts introduced in the matching DataCamp chapter. Complete the work in your own SQL rather than copying a finished query.

## Available tables

- `ex06_customers`
- `ex06_orders`

## Tasks

### Task 1

Create a reusable view that joins delivered orders to customer region, then return the view rows.

**Result requirements**

- **Return columns:** `order_id`, `customer_id`, `region`, `order_total`
- **Expected rows:** 12

### Task 2

Query the reusable view to summarize delivered revenue by region.

**Result requirements**

- **Return columns:** `region`, `delivered_revenue`

### Task 3

Create a physical snapshot table from the view and return its row count.

**Result requirements**

- **Return columns:** `snapshot_rows`
- **Expected rows:** 1

### Task 4

Compare the view and snapshot row counts to verify the snapshot was created correctly.

**Result requirements**

- **Return columns:** `view_rows`, `snapshot_rows`, `difference`
- **Expected rows:** 1
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
