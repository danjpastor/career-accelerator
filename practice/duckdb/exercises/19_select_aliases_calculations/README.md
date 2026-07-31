# DuckDB Exercise 02: Prepare a retail order review

**Week:** 3
**Estimated time:** 35 minutes
**Concepts:** column selection, aliases, arithmetic expressions, DISTINCT

## Purpose

Practice the SQL concepts introduced in the matching DataCamp chapter. Complete the work in your own SQL rather than copying a finished query.

## Available tables

- `ex02_retail_orders`

## Scenario

A retail operations manager is reviewing order data before it is used in a sales report. The manager needs a focused set of fields, clear report headings, and a quick check that stored revenue agrees with the order details.

## Tasks

### Task 1

Check what each order would be worth before discounts. Return `order_id`, `quantity`, `unit_price`, and `quantity * unit_price` as `line_value`.

**Result requirements**

- **Return columns:** `order_id`, `quantity`, `unit_price`, `line_value`
- **Expected rows:** 24

### Task 2

Prepare a sales report with consistent headings. Return `order_id`; rename `region` to `sales_region`, `sales_channel` to `channel`, and `revenue` to `recorded_revenue`.

**Result requirements**

- **Return columns:** `order_id`, `sales_region`, `channel`, `recorded_revenue`
- **Expected rows:** 24

### Task 3

Check whether the revenue stored for each order matches quantity multiplied by unit price. Return `order_id`, rename `revenue` to `recorded_revenue`, and calculate the difference as `revenue_difference`.

**Result requirements**

- **Return columns:** `order_id`, `recorded_revenue`, `revenue_difference`
- **Expected rows:** 24

### Task 4

List every region and sales-channel combination used by the business. Return unique `region` and `sales_channel` pairs, sorted by region and then sales channel.

**Result requirements**

- **Return columns:** `region`, `sales_channel`
- **Expected rows:** 12
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
