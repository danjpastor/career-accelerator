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

## Tasks

### Task 1

INNER JOIN customer accounts to tickets. Explain which customers disappear and why.

**Result requirements**

- **Return columns:** `count_star()`
- **Exact names for new columns:** `count_star()`
- **Expected rows:** 1

### Task 2

LEFT JOIN customer accounts to tickets. Explain why the row count differs from the INNER JOIN.

**Result requirements**

- **Return columns:** `count_star()`
- **Exact names for new columns:** `count_star()`
- **Expected rows:** 1

### Task 3

Use `ROW_NUMBER` to return the latest ticket for each customer.

**Result requirements**

- **Return columns:** `customer_id`, `ticket_id`
- **Expected rows:** 7

### Task 4

Rank agents by average resolution time using `DENSE_RANK`; lower is better.

**Result requirements**

- **Return columns:** `agent_id`, `avg_hours`, `performance_rank`
- **Exact names for new columns:** `avg_hours`, `performance_rank`
- **Expected rows:** 6

### Task 5

Calculate each agent's three-ticket rolling average resolution time.

**Result requirements**

- **Return columns:** `count_star()`
- **Exact names for new columns:** `count_star()`
- **Expected rows:** 1

### Task 6

Return customers without tickets.

**Result requirements**

- **Return columns:** `customer_id`
- **Expected rows:** 1

### Task 7

Write a 3–5 sentence explanation comparing aggregate queries with window-function queries.

**Result requirements**

- **Return columns:** `count_star()`
- **Exact names for new columns:** `count_star()`
- **Expected rows:** 1
## Completion evidence

1. Copy `starter.sql` to:
   `practice/duckdb/submissions/ex11_explain_joins_windows.sql`
2. Answer every question in that copied file.
3. Run each query successfully in DuckDB.
4. Compare your results with `validation.md` only after attempting the questions.
5. Add a short comment at the bottom explaining one decision or mistake you corrected.

The validation file contains result checkpoints, not completed SQL solutions.
