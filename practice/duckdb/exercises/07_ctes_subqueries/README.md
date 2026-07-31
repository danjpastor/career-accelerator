# DuckDB Exercise 12: Analyze order profitability with subqueries and CTEs

**Week:** 4
**Estimated time:** 50 minutes  
**Concepts:** subqueries, CTEs, layered analysis

## Scenario

A merchandising analyst must calculate order revenue, cost, and profit before identifying high-value orders and products.

## Tables

- `ex07_products`
- `ex07_orders`
- `ex07_order_items`

## Source CSV files

- `order_items.csv`
- `orders.csv`
- `products.csv`

## Tasks

### Task 1

Use a CTE to calculate revenue for every order.

**Result requirements**

- **Return columns:** `count_star()`, `round(sum(revenue), 2)`
- **Exact names for new columns:** `count_star()`, `round(sum(revenue), 2)`
- **Expected rows:** 1

### Task 2

Use a subquery to return orders whose revenue is above the average order revenue.

**Result requirements**

- **Return columns:** `order_id`
- **Expected rows:** 5

### Task 3

Use a CTE to calculate revenue, cost, and profit by order.

**Result requirements**

- **Return columns:** `count_star()`, `round(sum(profit), 2)`
- **Exact names for new columns:** `count_star()`, `round(sum(profit), 2)`
- **Expected rows:** 1

### Task 4

Calculate revenue and profit by product category.

**Result requirements**

- **Return columns:** `category`, `round(sum((i.quantity * i.sale_price)), 2)`, `round(sum((i.quantity * (i.sale_price - p.unit_cost))), 2)`
- **Exact names for new columns:** `round(sum((i.quantity * i.sale_price)), 2)`, `round(sum((i.quantity * (i.sale_price - p.unit_cost))), 2)`
- **Expected rows:** 4

### Task 5

Return the three products with the highest total profit.

**Result requirements**

- **Return columns:** `product_name`, `profit`
- **Exact names for new columns:** `profit`
- **Expected rows:** 3

### Task 6

Create two CTEs: one for order profitability and one for regional summaries.

**Result requirements**

- **Return columns:** `region`, `round(profit, 2)`
- **Exact names for new columns:** `round(profit, 2)`
- **Expected rows:** 4

### Task 7

Return regions whose total profit is above the average regional profit.

**Result requirements**

- **Return columns:** `region`
- **Expected rows:** 2
## Completion evidence

1. Copy `starter.sql` to:
   `practice/duckdb/submissions/ex07_ctes_subqueries.sql`
2. Answer every question in that copied file.
3. Run each query successfully in DuckDB.
4. Compare your results with `validation.md` only after attempting the questions.
5. Add a short comment at the bottom explaining one decision or mistake you corrected.

The validation file contains result checkpoints, not completed SQL solutions.
