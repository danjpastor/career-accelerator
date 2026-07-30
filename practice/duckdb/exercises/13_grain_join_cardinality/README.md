# DuckDB Exercise 09: Check table grain and join cardinality

**Week:** 4
**Estimated time:** 50 minutes  
**Concepts:** table grain, primary keys, join cardinality, pre-aggregation

## Scenario

An analyst joined order-level data to a one-to-many contact table and inflated revenue. Audit the table grains and build a safe result.

## Tables

- `ex13_accounts`
- `ex13_orders`
- `ex13_contacts`

## Questions

1. Task: Profile the row count and distinct business key count for each table. Required output: return only these columns in this order: `table_name`, `row_count`, `distinct_key_count`. Use these exact names for calculated or summarized columns: `table_name`, `row_count`, `distinct_key_count`. A correct result contains 3 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
2. Task: Find account IDs that appear more than once in the contacts table. Required output: return only these columns in this order: `account_id`, `contact_count`. Use these exact names for calculated or summarized columns: `contact_count`. A correct result contains 2 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
3. Task: Join orders directly to contacts and compare the resulting row count with the original order count. Required output: return only these columns in this order: `joined_rows`, `order_rows`. Use these exact names for calculated or summarized columns: `joined_rows`, `order_rows`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
4. Task: Calculate the multiplication factor created by the direct join. Required output: return only these columns in this order: `multiplication_factor`. Use these exact names for calculated or summarized columns: `multiplication_factor`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
5. Task: Pre-aggregate contacts to one row per account, then join that result to orders without changing the order grain. Required output: return only these columns in this order: `row_count`, `distinct_orders`. Use these exact names for calculated or summarized columns: `row_count`, `distinct_orders`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
6. Task: Find accounts with no orders. Required output: return only these columns in this order: `account_id`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
7. Task: Write a short SQL comment stating the grain of the safe final result. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
## Completion evidence

1. Work in the standard submission file created by Career Accelerator.
2. Answer every question and run each query successfully.
3. Use `validation.md` only after making a genuine attempt.
4. Add the requested explanation comments in your own words.

The validation file contains result checkpoints, not completed SQL solutions.
