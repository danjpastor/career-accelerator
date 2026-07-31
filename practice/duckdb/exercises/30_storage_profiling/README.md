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

## Scenario

A data analyst is deciding how several practice tables should be stored and queried. The first step is to profile their size, keys, and analytical grain.

## Tasks

### Task 1

List the practice tables available in the main schema.

**Result requirements**

- Return columns in this order: `table_name`.

### Task 2

Profile the row count and distinct business key count for the orders table.

**Result requirements**

- Return columns in this order: `row_count`, `distinct_order_ids`.
- Return 1 row.

### Task 3

Compare row count with distinct order IDs in the order-items table to describe its grain.

**Result requirements**

- Return columns in this order: `row_count`, `distinct_order_ids`.
- Return 1 row.

### Task 4

Create a compact table profile showing table name, row count, and stated analytical grain for three selected tables.

**Result requirements**

- Return columns in this order: `table_name`, `row_count`, `grain`.
- Return 3 rows.

## Complete the exercise

1. Complete each task in the SQL editor.
2. Use **Check Task** for specific feedback and hints.
3. Use **Check Exercise** after every task passes.
4. Select **Submit Exercise** to record completion.

## Common mistakes

- Using a concept before its prerequisite chapter is complete.
- Returning the right number of rows with the wrong grain.
- Leaving columns unqualified when more than one table contains the same name.
- Typing expected results instead of deriving them from the data.
