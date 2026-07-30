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

## Questions

1. Task: Combine the previous and current customer IDs with UNION. Required output: return only these columns in this order: `distinct_customer_count`. Use these exact names for calculated or summarized columns: `distinct_customer_count`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
2. Task: Combine both customer tables with UNION ALL and count all rows. Required output: return only these columns in this order: `all_row_count`. Use these exact names for calculated or summarized columns: `all_row_count`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
3. Task: Find customers present in both periods with INTERSECT. Required output: return only these columns in this order: `customer_id`. A correct result contains 4 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
4. Task: Find customers that are new in the current period with EXCEPT. Required output: return only these columns in this order: `customer_id`. A correct result contains 3 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
5. Task: Return current customers that have at least one order using a semi-join pattern. Required output: return only these columns in this order: `customer_id`. A correct result contains 3 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
6. Task: Return current customers with no orders using an anti-join pattern. Required output: return only these columns in this order: `customer_id`. A correct result contains 3 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
7. Task: Explain when UNION ALL is safer than UNION for audit work. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
## Completion evidence

1. Work in the standard submission file created by Career Accelerator.
2. Answer every question and run each query successfully.
3. Use `validation.md` only after making a genuine attempt.
4. Add the requested explanation comments in your own words.

The validation file contains result checkpoints, not completed SQL solutions.
