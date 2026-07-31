# DuckDB Exercise 26: Profile tables for analytical storage decisions

**Week:** 6
**Estimated time:** 45 minutes
**Concepts:** information_schema, table size, grain, OLTP versus OLAP reasoning

## Purpose

Practice the SQL concepts introduced in the matching DataCamp chapter. Complete the work in your own SQL rather than copying a finished query.

## Available tables

- `information_schema.tables`
- `ex06_orders`
- `ex07_order_items`

## Tasks

### Task 1

List the practice tables available in the main schema.

**Result requirements**

- **Return columns:** `table_name`

### Task 2

Profile the row count and distinct business key count for the orders table.

**Result requirements**

- **Return columns:** `row_count`, `distinct_order_ids`
- **Expected rows:** 1

### Task 3

Compare row count with distinct order IDs in the order-items table to describe its grain.

**Result requirements**

- **Return columns:** `row_count`, `distinct_order_ids`
- **Expected rows:** 1

### Task 4

Create a compact table profile showing table name, row count, and stated analytical grain for three selected tables.

**Result requirements**

- **Return columns:** `table_name`, `row_count`, `grain`
- **Expected rows:** 3
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
