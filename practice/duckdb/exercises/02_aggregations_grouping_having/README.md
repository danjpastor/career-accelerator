# DuckDB Exercise 02: Summarize retail orders

**Week:** 2  
**Estimated time:** 40 minutes  
**Concepts:** COUNT, SUM, AVG, GROUP BY, HAVING

## Scenario

A retail manager wants a concise summary of May sales by region, channel, and category.

## Tables

- `ex02_retail_orders`

## Source CSV files

- `retail_orders.csv`

## Questions

1. Count all orders.
2. Calculate total revenue.
3. Calculate average order revenue.
4. Return order count and revenue by region.
5. Return sales channels with more than five orders using `HAVING`.
6. Calculate average discount by product category.
7. Return the region with the highest total revenue.

## Completion evidence

1. Copy `starter.sql` to:
   `practice/duckdb/submissions/ex02_aggregations_grouping_having.sql`
2. Answer every question in that copied file.
3. Run each query successfully in DuckDB.
4. Compare your results with `validation.md` only after attempting the questions.
5. Add a short comment at the bottom explaining one decision or mistake you corrected.

The validation file contains result checkpoints, not completed SQL solutions.
