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

## Questions

1. Task: Document the grain and expected key for each table in SQL comments. Required output: return only these columns in this order: `table_name`, `row_count`. Use these exact names for calculated or summarized columns: `table_name`, `row_count`. A correct result contains 3 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
2. Task: Find duplicate order IDs and report their duplicate count. Required output: return only these columns in this order: `order_id`, `row_count`. Use these exact names for calculated or summarized columns: `row_count`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
3. Task: Find orders whose customer_id does not exist in customers. Required output: return only these columns in this order: `order_id`, `customer_id`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
4. Task: Find payments whose order_id does not exist in orders. Required output: return only these columns in this order: `payment_id`, `order_id`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
5. Task: Find required order fields that are NULL or blank. Required output: return only these columns in this order: `order_id`, `issue`. Use these exact names for calculated or summarized columns: `issue`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
6. Task: Reconcile order totals to payment amounts at one row per order and flag differences. Required output: return only these columns in this order: `order_id`, `difference`. Use these exact names for calculated or summarized columns: `difference`. A correct result contains 2 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
7. Task: Build one CTE-based quality summary with issue_type and issue_count. Required output: return only these columns in this order: `issue_type`, `issue_count`. Use these exact names for calculated or summarized columns: `issue_type`, `issue_count`. A correct result contains 5 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
8. Task: Write a three-sentence findings comment naming the highest-risk issue and the next action. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
## Completion evidence

1. Work in the standard submission file created by Career Accelerator.
2. Answer every question and run each query successfully.
3. Use `validation.md` only after making a genuine attempt.
4. Add the requested explanation comments in your own words.

The validation file contains result checkpoints, not completed SQL solutions.
