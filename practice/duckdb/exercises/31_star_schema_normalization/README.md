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

## Scenario

A reporting team wants to reshape operational customer and order data into a simple fact-and-dimension model without changing totals.

## Tasks

### Task 1

Return a customer dimension-style result with one row per customer.

**Result requirements**

- Return columns in this order: `customer_id`, `customer_name`, `region`, `signup_date`.
- Return 10 rows.

### Task 2

Return an order fact-style result with order measures and customer key.

**Result requirements**

- Return columns in this order: `order_id`, `customer_id`, `order_date`, `order_total`, `order_status`.
- Return 14 rows.

### Task 3

Join the proposed fact and dimension outputs to summarize revenue by region.

**Result requirements**

- Return columns in this order: `region`, `order_count`, `order_revenue`.
- Return 4 rows.

### Task 4

Validate that the dimension key remains unique and report any duplicates.

**Result requirements**

- Return columns in this order: `customer_id`, `duplicate_count`.
- Return 0 rows.

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
