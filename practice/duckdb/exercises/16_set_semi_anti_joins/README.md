# DuckDB Exercise 08: Compare customer groups with set logic

**Week:** 4
**Estimated time:** 45 minutes  
**Concepts:** UNION, INTERSECT, EXCEPT, semi joins, anti joins

## Scenario

Customer success needs to compare old and current customer populations and identify who did or did not purchase.

## Tables

- `ex16_previous_customers`
- `ex16_current_customers`
- `ex16_orders`

## Tasks

### Task 1

Combine the previous and current customer IDs with UNION.

**Result requirements**

- **Return columns:** `distinct_customer_count`
- **Exact names for new columns:** `distinct_customer_count`
- **Expected rows:** 1

### Task 2

Combine both customer tables with UNION ALL and count all rows.

**Result requirements**

- **Return columns:** `all_row_count`
- **Exact names for new columns:** `all_row_count`
- **Expected rows:** 1

### Task 3

Find customers present in both periods with INTERSECT.

**Result requirements**

- **Return columns:** `customer_id`
- **Expected rows:** 4

### Task 4

Find customers that are new in the current period with EXCEPT.

**Result requirements**

- **Return columns:** `customer_id`
- **Expected rows:** 3

### Task 5

Return current customers that have at least one order using a semi-join pattern.

**Result requirements**

- **Return columns:** `customer_id`
- **Expected rows:** 3

### Task 6

Return current customers with no orders using an anti-join pattern.

**Result requirements**

- **Return columns:** `customer_id`
- **Expected rows:** 3

### Task 7

Explain when UNION ALL is safer than UNION for audit work.

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
