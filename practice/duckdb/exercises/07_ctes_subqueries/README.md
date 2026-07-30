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

## Questions

1. Task: Use a CTE to calculate revenue for every order. Required output: return only these columns in this order: `count_star()`, `round(sum(revenue), 2)`. Use these exact names for calculated or summarized columns: `count_star()`, `round(sum(revenue), 2)`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
2. Task: Use a subquery to return orders whose revenue is above the average order revenue. Required output: return only these columns in this order: `order_id`. A correct result contains 5 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
3. Task: Use a CTE to calculate revenue, cost, and profit by order. Required output: return only these columns in this order: `count_star()`, `round(sum(profit), 2)`. Use these exact names for calculated or summarized columns: `count_star()`, `round(sum(profit), 2)`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
4. Task: Calculate revenue and profit by product category. Required output: return only these columns in this order: `category`, `round(sum((i.quantity * i.sale_price)), 2)`, `round(sum((i.quantity * (i.sale_price - p.unit_cost))), 2)`. Use these exact names for calculated or summarized columns: `round(sum((i.quantity * i.sale_price)), 2)`, `round(sum((i.quantity * (i.sale_price - p.unit_cost))), 2)`. A correct result contains 4 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
5. Task: Return the three products with the highest total profit. Required output: return only these columns in this order: `product_name`, `profit`. Use these exact names for calculated or summarized columns: `profit`. A correct result contains 3 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
6. Task: Create two CTEs: one for order profitability and one for regional summaries. Required output: return only these columns in this order: `region`, `round(profit, 2)`. Use these exact names for calculated or summarized columns: `round(profit, 2)`. A correct result contains 4 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
7. Task: Return regions whose total profit is above the average regional profit. Required output: return only these columns in this order: `region`. A correct result contains 2 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
## Completion evidence

1. Copy `starter.sql` to:
   `practice/duckdb/submissions/ex07_ctes_subqueries.sql`
2. Answer every question in that copied file.
3. Run each query successfully in DuckDB.
4. Compare your results with `validation.md` only after attempting the questions.
5. Add a short comment at the bottom explaining one decision or mistake you corrected.

The validation file contains result checkpoints, not completed SQL solutions.
