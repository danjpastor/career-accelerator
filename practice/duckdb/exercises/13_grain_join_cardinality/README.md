# DuckDB Exercise 09: Audit table grain and join cardinality

**Week:** 4
**Estimated time:** 50 minutes  
**Concepts:** table grain, primary keys, join cardinality, pre-aggregation

## Scenario

An analyst joined order-level data to a one-to-many contact table and accidentally inflated revenue. Audit the table grains and rebuild the analysis safely.

## Tables

- `ex13_accounts`
- `ex13_orders`
- `ex13_contacts`

## Tasks

### Task 1

Profile the row count and distinct business key count for each table.

**Result requirements**

- Return columns in this order: `table_name`, `row_count`, `distinct_key_count`.
- Return 3 rows.

### Task 2

Find account IDs that appear more than once in the contacts table.

**Result requirements**

- Return columns in this order: `account_id`, `contact_count`.
- Return 2 rows.

### Task 3

Join orders directly to contacts and compare the resulting row count with the original order count.

**Result requirements**

- Return columns in this order: `joined_rows`, `order_rows`.
- Return 1 row.

### Task 4

Calculate the multiplication factor created by the direct join.

**Result requirements**

- Return columns in this order: `multiplication_factor`.
- Return 1 row.

### Task 5

Pre-aggregate contacts to one row per account, then join that result to orders without changing the order grain.

**Result requirements**

- Return columns in this order: `row_count`, `distinct_orders`.
- Return 1 row.

### Task 6

Find accounts with no orders.

**Result requirements**

- Return columns in this order: `account_id`.
- Return 1 row.

### Task 7

Add a SQL comment stating the grain of the safe final result, then return its row count as `safe_result_rows`.

**Result requirements**

- Return columns in this order: `safe_result_rows`.
- Return 1 row.

## Complete the exercise

1. Complete each task in the SQL editor.
2. Use **Check Task** for specific feedback and hints.
3. Use **Check Exercise** after every task passes.
4. Select **Submit Exercise** to record completion.

