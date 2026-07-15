# DuckDB Exercise 06: Join customers, orders, and payments

**Week:** 6  
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

1. INNER JOIN customers to orders and return customer name with each order.
2. LEFT JOIN customers to orders so customers without orders remain visible.
3. Find customers with no orders.
4. Join orders to payments and identify orders with no payment.
5. Create a three-table result with customer, order total, payment amount, and payment method.
6. Calculate delivered-order revenue by region.
7. Calculate customer lifetime delivered revenue, including customers with zero.

## Completion evidence

1. Copy `starter.sql` to:
   `practice/duckdb/submissions/ex06_joins.sql`
2. Answer every question in that copied file.
3. Run each query successfully in DuckDB.
4. Compare your results with `validation.md` only after attempting the questions.
5. Add a short comment at the bottom explaining one decision or mistake you corrected.

The validation file contains result checkpoints, not completed SQL solutions.
