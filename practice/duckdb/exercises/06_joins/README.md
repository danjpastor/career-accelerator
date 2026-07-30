# DuckDB Exercise 06: Combine customers, orders, and payments

**Week:** 4
**Estimated time:** 45 minutes  
**Concepts:** INNER JOIN, LEFT JOIN, multi-table joins

## Scenario

Finance and customer success need one view combining customer, order, and payment information.

## Tables

- `ex06_customers`
- `ex06_orders`
- `ex06_payments`

## Source CSV files

- `customers.csv`
- `orders.csv`
- `payments.csv`

## Questions

1. Task: INNER JOIN customers to orders and return customer name with each order. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
2. Task: LEFT JOIN customers to orders so customers without orders remain visible. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
3. Task: Find customers with no orders. Required output: return only these columns in this order: `customer_id`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
4. Task: Join orders to payments and identify orders with no payment. Required output: return only these columns in this order: `order_id`. A correct result contains 2 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
5. Task: Create a three-table result with customer, order total, payment amount, and payment method. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
6. Task: Calculate delivered-order revenue by region. Required output: return only these columns in this order: `region`, `sum(o.order_total)`. Use these exact names for calculated or summarized columns: `sum(o.order_total)`. A correct result contains 4 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
7. Task: Calculate customer lifetime delivered revenue, including customers with zero. Required output: return only these columns in this order: `customer_id`, `revenue`. Use these exact names for calculated or summarized columns: `revenue`. A correct result contains 10 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
## Completion evidence

1. Copy `starter.sql` to:
   `practice/duckdb/submissions/ex06_joins.sql`
2. Answer every question in that copied file.
3. Run each query successfully in DuckDB.
4. Compare your results with `validation.md` only after attempting the questions.
5. Add a short comment at the bottom explaining one decision or mistake you corrected.

The validation file contains result checkpoints, not completed SQL solutions.
