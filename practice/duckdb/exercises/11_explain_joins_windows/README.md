# DuckDB Exercise 18: Explain join and window-function results

**Week:** 5
**Estimated time:** 45 minutes  
**Concepts:** join reasoning, window reasoning, analyst communication

## Scenario

You must produce correct SQL and explain why the chosen join or window function is appropriate.

## Tables

- `ex11_customer_accounts`
- `ex11_support_agents`
- `ex11_tickets`

## Source CSV files

- `customer_accounts.csv`
- `support_agents.csv`
- `tickets.csv`

## Questions

1. Task: INNER JOIN customer accounts to tickets. Explain which customers disappear and why. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
2. Task: LEFT JOIN customer accounts to tickets. Explain why the row count differs from the INNER JOIN. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
3. Task: Use `ROW_NUMBER` to return the latest ticket for each customer. Required output: return only these columns in this order: `customer_id`, `ticket_id`. A correct result contains 7 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
4. Task: Rank agents by average resolution time using `DENSE_RANK`; lower is better. Required output: return only these columns in this order: `agent_id`, `avg_hours`, `performance_rank`. Use these exact names for calculated or summarized columns: `avg_hours`, `performance_rank`. A correct result contains 6 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
5. Task: Calculate each agent's three-ticket rolling average resolution time. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
6. Task: Return customers without tickets. Required output: return only these columns in this order: `customer_id`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
7. Task: Write a 3–5 sentence explanation comparing aggregate queries with window-function queries. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
## Completion evidence

1. Copy `starter.sql` to:
   `practice/duckdb/submissions/ex11_explain_joins_windows.sql`
2. Answer every question in that copied file.
3. Run each query successfully in DuckDB.
4. Compare your results with `validation.md` only after attempting the questions.
5. Add a short comment at the bottom explaining one decision or mistake you corrected.

The validation file contains result checkpoints, not completed SQL solutions.
