# DuckDB Exercise 07: Compare outer, cross, and self joins

**Week:** 4
**Estimated time:** 45 minutes
**Concepts:** LEFT JOIN, FULL JOIN, CROSS JOIN, SELF JOIN

## Purpose

Practice the SQL concepts introduced in the matching DataCamp chapter. Complete the work in your own SQL rather than copying a finished query.

## Available tables

- `ex06_customers`
- `ex06_orders`
- `ex10_employees`
- `ex10_departments`

## Scenario

An operations analyst must preserve unmatched records, connect employees to managers, and build planning combinations without losing information.

## Tasks

### Task 1

Use a left join to show every customer and any related orders, keeping customers with no order.

**Result requirements**

- Return columns in this order: `customer_id`, `customer_name`, `order_id`, `order_total`.
- Return 15 rows.

### Task 2

Use a full join to identify customer IDs that appear on only one side of the customer-order relationship.

**Result requirements**

- Return columns in this order: `customer_id`, `customer_name`, `order_id`, `relationship_status`.

### Task 3

Use a self join to show each employee beside their manager name when one exists.

**Result requirements**

- Return columns in this order: `employee_id`, `employee_name`, `manager_name`.
- Return 12 rows.

### Task 4

Use a cross join to build every combination of department and two named planning scenarios.

**Result requirements**

- Return columns in this order: `department_name`, `scenario`.
- Return 8 rows.

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
