# DuckDB Exercise 05: Connect orders to customers with inner joins

**Week:** 3
**Estimated time:** 40 minutes
**Concepts:** INNER JOIN, join keys, qualified columns, joined filters

## Purpose

Practice the SQL concepts introduced in the matching DataCamp chapter. Complete the work in your own SQL rather than copying a finished query.

## Available tables

- `ex06_customers`
- `ex06_orders`
- `ex06_payments`

## Scenario

A sales analyst needs to connect customers, orders, and payments so the business can report delivered sales and regional revenue.

## Tasks

### Task 1

Join orders to customers and return one row per matched order with customer name and region.

**Result requirements**

- Return columns in this order: `order_id`, `customer_name`, `region`, `order_total`.
- Return 14 rows.

### Task 2

Return only delivered orders after joining orders to customers.

**Result requirements**

- Return columns in this order: `order_id`, `customer_name`, `order_status`.
- Return 12 rows.

### Task 3

Join payments to orders and return the payment amount beside the order total.

**Result requirements**

- Return columns in this order: `payment_id`, `order_id`, `amount`, `order_total`.
- Return 12 rows.

### Task 4

Summarize matched order revenue by customer region.

**Result requirements**

- Return columns in this order: `region`, `order_count`, `order_revenue`.
- Return 4 rows.

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
