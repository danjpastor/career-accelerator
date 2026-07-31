# DuckDB Exercise 33: Complete the final relational data-quality audit

**Week:** 7
**Estimated time:** 65 minutes  
**Concepts:** grain, duplicates, NULLs, referential integrity, reconciliation, CTEs

## Scenario

Before portfolio analysis begins, complete a full quality audit across related customer, order, and payment tables.

## Tables

- `ex18_customers`
- `ex18_orders`
- `ex18_payments`

## Tasks

### Task 1

Document the grain and expected key for each table in SQL comments.

**Result requirements**

- **Return columns:** `table_name`, `row_count`
- **Exact names for new columns:** `table_name`, `row_count`
- **Expected rows:** 3

### Task 2

Find duplicate order IDs and report their duplicate count.

**Result requirements**

- **Return columns:** `order_id`, `row_count`
- **Exact names for new columns:** `row_count`
- **Expected rows:** 1

### Task 3

Find orders whose customer_id does not exist in customers.

**Result requirements**

- **Return columns:** `order_id`, `customer_id`
- **Expected rows:** 1

### Task 4

Find payments whose order_id does not exist in orders.

**Result requirements**

- **Return columns:** `payment_id`, `order_id`
- **Expected rows:** 1

### Task 5

Find required order fields that are NULL or blank.

**Result requirements**

- **Return columns:** `order_id`, `issue`
- **Exact names for new columns:** `issue`
- **Expected rows:** 1

### Task 6

Reconcile order totals to payment amounts at one row per order and flag differences.

**Result requirements**

- **Return columns:** `order_id`, `difference`
- **Exact names for new columns:** `difference`
- **Expected rows:** 2

### Task 7

Build one CTE-based quality summary with issue_type and issue_count.

**Result requirements**

- **Return columns:** `issue_type`, `issue_count`
- **Exact names for new columns:** `issue_type`, `issue_count`
- **Expected rows:** 5

### Task 8

Write a three-sentence findings comment naming the highest-risk issue and the next action.

**Result requirements**

- **Return columns:** `count_star()`
- **Exact names for new columns:** `count_star()`
- **Expected rows:** 1
## Completion evidence

1. Work in the standard submission file created by Career Accelerator.
2. Answer every question and run each query successfully.
3. Use `validation.md` only after making a genuine attempt.
4. Add the requested explanation comments in your own words.

The validation file contains result checkpoints, not completed SQL solutions.
