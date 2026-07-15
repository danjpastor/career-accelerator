# DuckDB Exercise 11: Explain joins and window functions

**Week:** 12  
**Estimated time:** 45 minutes  
**Concepts:** LEFT JOIN, ROW_NUMBER, DENSE_RANK, rolling averages

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

1. INNER JOIN customer accounts to tickets. Explain which customers disappear and why.
2. LEFT JOIN customer accounts to tickets. Explain why the row count differs from the INNER JOIN.
3. Use `ROW_NUMBER` to return the latest ticket for each customer.
4. Rank agents by average resolution time using `DENSE_RANK`; lower is better.
5. Calculate each agent's three-ticket rolling average resolution time.
6. Return customers without tickets.
7. Write a 3–5 sentence explanation comparing aggregate queries with window-function queries.

## Completion evidence

1. Copy `starter.sql` to:
   `practice/duckdb/submissions/ex11_explain_joins_windows.sql`
2. Answer every question in that copied file.
3. Run each query successfully in DuckDB.
4. Compare your results with `validation.md` only after attempting the questions.
5. Add a short comment at the bottom explaining one decision or mistake you corrected.

The validation file contains result checkpoints, not completed SQL solutions.
