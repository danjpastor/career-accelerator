# Multi-Table Joins and Aliases

Real analysis often follows a chain of relationships. Build that chain one join at a time and keep every alias meaningful.

:::columns
:::column
> **Learning Goals:**
> ✓ Trace a path across three or more tables.
> ✓ Join each table through the correct key.
> ✓ Avoid ambiguous column names with clear aliases.
:::column
```sql
SELECT
    t.ticket_id,
    a.agent_name,
    tm.team_name,
    d.department_name
FROM support_tickets AS t
INNER JOIN support_agents AS a
    ON t.assigned_agent_id = a.agent_id
INNER JOIN support_teams AS tm
    ON a.team_id = tm.team_id
INNER JOIN departments AS d
    ON tm.department_id = d.department_id;
```
:::

## Read the relationship chain

```text
support_tickets → support_agents → support_teams → departments
```

Each arrow represents a different key comparison.

## Add one join at a time

1. Join two tables.
2. Run the query and inspect row count and sample rows.
3. Add the next table.
4. Recheck the grain.
5. Add filters only after the relationship is correct.

## Alias preferences

Use short, recognizable aliases that communicate the table role. Avoid aliases so cryptic that they hide the model.

> **Key Idea:** Every added one-to-many relationship can multiply rows. The final result’s grain is determined by the most detailed table selected.
