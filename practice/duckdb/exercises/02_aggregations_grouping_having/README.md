# DuckDB Exercise 04: Summarize retail orders with grouped metrics

**Week:** 3
**Estimated time:** 40 minutes  
**Concepts:** COUNT, SUM, AVG, GROUP BY, HAVING

## Scenario

A sales manager needs a short weekly summary of the retail order file. The report should show overall performance, regional results, channel volume, and discount patterns.

## Tables

- `ex02_retail_orders`

## Source CSV files

- `retail_orders.csv`

## Tasks

### Task 1

Count the orders in the sales file. Return the count as `orders`.

**Result requirements**

- **Return columns:** `orders`
- **Exact names for new columns:** `orders`
- **Expected rows:** 1

### Task 2

Calculate the revenue recorded across all orders. Return it as `revenue`.

**Result requirements**

- **Return columns:** `revenue`
- **Expected rows:** 1

### Task 3

Calculate the average revenue per order. Return it as `average_revenue`.

**Result requirements**

- **Return columns:** `average_revenue`
- **Exact names for new columns:** `average_revenue`
- **Expected rows:** 1

### Task 4

Show order volume and revenue for each region. Return `region`, the order count as `orders`, and total revenue as `revenue`.

**Result requirements**

- **Return columns:** `region`, `orders`, `revenue`
- **Exact names for new columns:** `orders`
- **Expected rows:** 4

### Task 5

Find sales channels that handled more than five orders. Return `sales_channel` and the order count as `orders`.

**Result requirements**

- **Return columns:** `sales_channel`, `orders`
- **Exact names for new columns:** `orders`
- **Expected rows:** 2

### Task 6

Calculate the average discount for each product category. Return `product_category` and the average as `average_discount`.

**Result requirements**

- **Return columns:** `product_category`, `average_discount`
- **Exact names for new columns:** `average_discount`
- **Expected rows:** 4

### Task 7

Find the region that generated the most revenue. Return `region` and total `revenue`.

**Result requirements**

- **Return columns:** `region`, `revenue`
- **Expected rows:** 1
## Completion evidence

1. Copy `starter.sql` to:
   `practice/duckdb/submissions/ex02_aggregations_grouping_having.sql`
2. Answer every question in that copied file.
3. Run each query successfully in DuckDB.
4. Compare your results with `validation.md` only after attempting the questions.
5. Add a short comment at the bottom explaining one decision or mistake you corrected.

The validation file contains result checkpoints, not completed SQL solutions.
