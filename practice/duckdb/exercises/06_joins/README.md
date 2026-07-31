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

## Tasks

### Task 1

INNER JOIN customers to orders and return customer name with each order.

**Result requirements**

- **Return columns:** `count_star()`
- **Exact names for new columns:** `count_star()`
- **Expected rows:** 1

### Task 2

LEFT JOIN customers to orders so customers without orders remain visible.

**Result requirements**

- **Return columns:** `count_star()`
- **Exact names for new columns:** `count_star()`
- **Expected rows:** 1

### Task 3

Find customers with no orders.

**Result requirements**

- **Return columns:** `customer_id`
- **Expected rows:** 1

### Task 4

Join orders to payments and identify orders with no payment.

**Result requirements**

- **Return columns:** `order_id`
- **Expected rows:** 2

### Task 5

Create a three-table result with customer, order total, payment amount, and payment method.

**Result requirements**

- **Return columns:** `count_star()`
- **Exact names for new columns:** `count_star()`
- **Expected rows:** 1

### Task 6

Calculate delivered-order revenue by region.

**Result requirements**

- **Return columns:** `region`, `sum(o.order_total)`
- **Exact names for new columns:** `sum(o.order_total)`
- **Expected rows:** 4

### Task 7

Calculate customer lifetime delivered revenue, including customers with zero.

**Result requirements**

- **Return columns:** `customer_id`, `revenue`
- **Exact names for new columns:** `revenue`
- **Expected rows:** 10
## Completion evidence

1. Copy `starter.sql` to:
   `practice/duckdb/submissions/ex06_joins.sql`
2. Answer every question in that copied file.
3. Run each query successfully in DuckDB.
4. Compare your results with `validation.md` only after attempting the questions.
5. Add a short comment at the bottom explaining one decision or mistake you corrected.

The validation file contains result checkpoints, not completed SQL solutions.
