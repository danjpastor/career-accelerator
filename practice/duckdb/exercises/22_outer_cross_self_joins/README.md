# DuckDB Exercise 07: Use outer, cross, and self joins

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

## Questions

1. Task: Use a left join to show every customer and any related orders, keeping customers with no order. Required output: return only these columns in this order: `customer_id`, `customer_name`, `order_id`, `order_total`. A correct result contains 15 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
2. Task: Use a full join to identify customer IDs that appear on only one side of the customer-order relationship. Required output: return only these columns in this order: `customer_id`, `customer_name`, `order_id`, `relationship_status`. Do not include extra columns; keep every filter and sort rule stated in the task.
3. Task: Use a self join to show each employee beside their manager name when one exists. Required output: return only these columns in this order: `employee_id`, `employee_name`, `manager_name`. A correct result contains 12 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
4. Task: Use a cross join to build every combination of department and two named planning scenarios. Required output: return only these columns in this order: `department_name`, `scenario`. A correct result contains 8 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
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
