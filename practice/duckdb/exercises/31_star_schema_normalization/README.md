# DuckDB Exercise 27: Reshape operational data into analytical tables

**Week:** 6
**Estimated time:** 50 minutes
**Concepts:** fact tables, dimensions, normalization, star-schema joins

## Purpose

Practice the SQL concepts introduced in the matching DataCamp chapter. Complete the work in your own SQL rather than copying a finished query.

## Available tables

- `ex06_customers`
- `ex06_orders`
- `ex06_payments`

## Tasks

### Task 1

Return a customer dimension-style result with one row per customer.

**Result requirements**

- **Return columns:** `customer_id`, `customer_name`, `region`, `signup_date`
- **Expected rows:** 10

### Task 2

Return an order fact-style result with order measures and customer key.

**Result requirements**

- **Return columns:** `order_id`, `customer_id`, `order_date`, `order_total`, `order_status`
- **Expected rows:** 14

### Task 3

Join the proposed fact and dimension outputs to summarize revenue by region.

**Result requirements**

- **Return columns:** `region`, `order_count`, `order_revenue`
- **Expected rows:** 4

### Task 4

Validate that the dimension key remains unique and report any duplicates.

**Result requirements**

- **Return columns:** `customer_id`, `duplicate_count`
- **Expected rows:** 0
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
