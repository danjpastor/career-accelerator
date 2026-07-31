# DuckDB Exercise 33: Complete a full relational data-quality audit

**Week:** 6
**Estimated time:** 65 minutes  
**Concepts:** grain, duplicates, NULLs, referential integrity, reconciliation, CTEs

## Scenario

Before portfolio analysis begins, the data team needs a complete quality audit across related customer, order, and payment tables.

## Tables

- `ex18_customers`
- `ex18_orders`
- `ex18_payments`

## Tasks

### Task 1

Document the grain and expected key for each table in SQL comments.

**Result requirements**

- Return columns in this order: `table_name`, `row_count`.
- Return 3 rows.

### Task 2

Find duplicate order IDs and report their duplicate count.

**Result requirements**

- Return columns in this order: `order_id`, `row_count`.
- Return 1 row.

### Task 3

Find orders whose customer_id does not exist in customers.

**Result requirements**

- Return columns in this order: `order_id`, `customer_id`.
- Return 1 row.

### Task 4

Find payments whose order_id does not exist in orders.

**Result requirements**

- Return columns in this order: `payment_id`, `order_id`.
- Return 1 row.

### Task 5

Find required order fields that are NULL or blank.

**Result requirements**

- Return columns in this order: `order_id`, `issue`.
- Return 1 row.

### Task 6

Reconcile order totals to payment amounts at one row per order and flag differences.

**Result requirements**

- Return columns in this order: `order_id`, `difference`.
- Return 2 rows.

### Task 7

Build one CTE-based quality summary with issue_type and issue_count.

**Result requirements**

- Return columns in this order: `issue_type`, `issue_count`.
- Return 5 rows.

### Task 8

Write a three-sentence SQL comment naming the highest-risk data issue and the next action, then return the total audit row count as `audit_rows`.

**Result requirements**

- Return columns in this order: `audit_rows`.
- Return 1 row.

## Complete the exercise

1. Complete each task in the SQL editor.
2. Use **Check Task** for specific feedback and hints.
3. Use **Check Exercise** after every task passes.
4. Select **Submit Exercise** to record completion.

