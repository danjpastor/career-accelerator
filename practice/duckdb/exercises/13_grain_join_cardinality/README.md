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

## Tasks

### Task 1

Profile the row count and distinct business key count for each table.

**Result requirements**

- **Return columns:** `table_name`, `row_count`, `distinct_key_count`
- **Exact names for new columns:** `table_name`, `row_count`, `distinct_key_count`
- **Expected rows:** 3

### Task 2

Find account IDs that appear more than once in the contacts table.

**Result requirements**

- **Return columns:** `account_id`, `contact_count`
- **Exact names for new columns:** `contact_count`
- **Expected rows:** 2

### Task 3

Join orders directly to contacts and compare the resulting row count with the original order count.

**Result requirements**

- **Return columns:** `joined_rows`, `order_rows`
- **Exact names for new columns:** `joined_rows`, `order_rows`
- **Expected rows:** 1

### Task 4

Calculate the multiplication factor created by the direct join.

**Result requirements**

- **Return columns:** `multiplication_factor`
- **Exact names for new columns:** `multiplication_factor`
- **Expected rows:** 1

### Task 5

Pre-aggregate contacts to one row per account, then join that result to orders without changing the order grain.

**Result requirements**

- **Return columns:** `row_count`, `distinct_orders`
- **Exact names for new columns:** `row_count`, `distinct_orders`
- **Expected rows:** 1

### Task 6

Find accounts with no orders.

**Result requirements**

- **Return columns:** `account_id`
- **Expected rows:** 1

### Task 7

Write a short SQL comment stating the grain of the safe final result.

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
