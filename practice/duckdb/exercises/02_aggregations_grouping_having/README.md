# DuckDB Exercise 04: Summarize retail orders with grouped metrics

**Week:** 3
**Estimated time:** 40 minutes  
**Concepts:** COUNT, SUM, AVG, GROUP BY, HAVING

## Scenario

A retail manager wants a concise summary of May sales by region, channel, and category.

## Tables

- `ex02_retail_orders`

## Source CSV files

- `retail_orders.csv`

## Questions

1. Task: Count all orders. Required output: return only these columns in this order: `orders`. Use these exact names for calculated or summarized columns: `orders`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
2. Task: Calculate total revenue. Required output: return only these columns in this order: `revenue`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
3. Task: Calculate average order revenue. Required output: return only these columns in this order: `average_revenue`. Use these exact names for calculated or summarized columns: `average_revenue`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
4. Task: Return order count and revenue by region. Required output: return only these columns in this order: `region`, `orders`, `revenue`. Use these exact names for calculated or summarized columns: `orders`. A correct result contains 4 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
5. Task: Return sales channels with more than five orders using `HAVING`. Required output: return only these columns in this order: `sales_channel`, `orders`. Use these exact names for calculated or summarized columns: `orders`. A correct result contains 2 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
6. Task: Calculate average discount by product category. Required output: return only these columns in this order: `product_category`, `average_discount`. Use these exact names for calculated or summarized columns: `average_discount`. A correct result contains 4 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
7. Task: Return the region with the highest total revenue. Required output: return only these columns in this order: `region`, `revenue`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
## Completion evidence

1. Copy `starter.sql` to:
   `practice/duckdb/submissions/ex02_aggregations_grouping_having.sql`
2. Answer every question in that copied file.
3. Run each query successfully in DuckDB.
4. Compare your results with `validation.md` only after attempting the questions.
5. Add a short comment at the bottom explaining one decision or mistake you corrected.

The validation file contains result checkpoints, not completed SQL solutions.
