# DuckDB Exercise 07: Analyze order profitability

**Week:** 6  
**Estimated time:** 50 minutes  
**Concepts:** subqueries, CTEs, multi-step analysis

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

1. Use a CTE to calculate revenue for every order.
2. Use a subquery to return orders whose revenue is above the average order revenue.
3. Use a CTE to calculate revenue, cost, and profit by order.
4. Calculate revenue and profit by product category.
5. Return the three products with the highest total profit.
6. Create two CTEs: one for order profitability and one for regional summaries.
7. Return regions whose total profit is above the average regional profit.

## Completion evidence

1. Copy `starter.sql` to:
   `practice/duckdb/submissions/ex07_ctes_subqueries.sql`
2. Answer every question in that copied file.
3. Run each query successfully in DuckDB.
4. Compare your results with `validation.md` only after attempting the questions.
5. Add a short comment at the bottom explaining one decision or mistake you corrected.

The validation file contains result checkpoints, not completed SQL solutions.
