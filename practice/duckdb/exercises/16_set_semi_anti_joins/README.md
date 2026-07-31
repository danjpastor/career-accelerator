# DuckDB Exercise 08: Compare customer populations with set and existence logic

**Week:** 4
**Estimated time:** 45 minutes  
**Concepts:** UNION, INTERSECT, EXCEPT, semi joins, anti joins

## Scenario

Customer Success needs to compare previous and current customer lists and identify customers who did or did not place an order.

## Tables

- `ex16_previous_customers`
- `ex16_current_customers`
- `ex16_orders`

## Tasks

### Task 1

Combine the previous and current customer IDs with UNION.

**Result requirements**

- Return columns in this order: `distinct_customer_count`.
- Return 1 row.

### Task 2

Combine both customer tables with UNION ALL and count all rows.

**Result requirements**

- Return columns in this order: `all_row_count`.
- Return 1 row.

### Task 3

Find customers present in both periods with INTERSECT.

**Result requirements**

- Return columns in this order: `customer_id`.
- Return 4 rows.

### Task 4

Find customers that are new in the current period with EXCEPT.

**Result requirements**

- Return columns in this order: `customer_id`.
- Return 3 rows.

### Task 5

Return current customers that have at least one order using a semi-join pattern.

**Result requirements**

- Return columns in this order: `customer_id`.
- Return 3 rows.

### Task 6

Return current customers with no orders using an anti-join pattern.

**Result requirements**

- Return columns in this order: `customer_id`.
- Return 3 rows.

### Task 7

Add a SQL comment explaining when `UNION ALL` is safer than `UNION` for audit work, then return the combined customer row count as `customer_rows`.

**Result requirements**

- Return columns in this order: `customer_rows`.
- Return 1 row.

## Complete the exercise

1. Complete each task in the SQL editor.
2. Use **Check Task** for specific feedback and hints.
3. Use **Check Exercise** after every task passes.
4. Select **Submit Exercise** to record completion.

