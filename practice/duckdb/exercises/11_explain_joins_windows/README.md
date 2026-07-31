# DuckDB Exercise 18: Explain joins and window functions

**Week:** 5
**Estimated time:** 45 minutes  
**Concepts:** join reasoning, window reasoning, analyst communication

## Scenario

A senior analyst is reviewing your SQL for a customer-support report. You must produce the correct result and explain why each join or window function is appropriate.

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

Use an inner join between customer accounts and tickets. Return the joined row count as `inner_join_rows` and add a SQL comment explaining which customers disappear and why.

**Result requirements**

- Return columns in this order: `inner_join_rows`.
- Return 1 row.

### Task 2

Use a left join between customer accounts and tickets. Return the joined row count as `left_join_rows` and add a SQL comment explaining why it differs from the inner join.

**Result requirements**

- Return columns in this order: `left_join_rows`.
- Return 1 row.

### Task 3

Use `ROW_NUMBER` to return the latest ticket for each customer.

**Result requirements**

- Return columns in this order: `customer_id`, `ticket_id`.
- Return 7 rows.

### Task 4

Rank agents by average resolution time using `DENSE_RANK`; lower is better.

**Result requirements**

- Return columns in this order: `agent_id`, `avg_hours`, `performance_rank`.
- Return 6 rows.

### Task 5

Calculate each agent’s trailing three-ticket average resolution time, then return the number of result rows as `rolling_average_rows`.

**Result requirements**

- Return columns in this order: `rolling_average_rows`.
- Return 1 row.

### Task 6

Return customers without tickets.

**Result requirements**

- Return columns in this order: `customer_id`.
- Return 1 row.

### Task 7

Write a 3–5 sentence SQL comment comparing aggregate queries with window-function queries, then return the ticket row count as `comparison_rows`.

**Result requirements**

- Return columns in this order: `comparison_rows`.
- Return 1 row.

## Complete the exercise

1. Complete each task in the SQL editor.
2. Use **Check Task** for specific feedback and hints.
3. Use **Check Exercise** after every task passes.
4. Select **Submit Exercise** to record completion.

