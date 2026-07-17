# INNER JOIN: Keep the Matches

`INNER JOIN` returns only row combinations for which the `ON` condition is true. Rows without a partner disappear from the result.

:::columns
:::column
> **Learning Goals:**
> ✓ Explain why unmatched rows disappear.
> ✓ Use aliases to identify columns clearly.
> ✓ Separate the relationship in `ON` from filters in `WHERE`.
:::column
```sql
SELECT
    t.ticket_id,
    a.agent_name,
    t.resolution_minutes
FROM support_tickets AS t
INNER JOIN support_agents AS a
    ON t.assigned_agent_id = a.agent_id
WHERE t.status = 'Closed';
```
:::

## What is preserved?

With an `INNER JOIN`, neither table is guaranteed to be preserved. A row survives only when a match exists on both sides.

| Situation | Returned by `INNER JOIN`? |
|---|---|
| Ticket has a matching agent | Yes |
| Agent has no tickets | No |
| Ticket references an unknown agent | No |
| Join key is `NULL` | No equality match |

## Think in pairs

Suppose one agent owns three tickets. The agent row can match three times, producing three output rows.

```sql
SELECT
    a.agent_id,
    a.agent_name,
    t.ticket_id
FROM support_agents AS a
INNER JOIN support_tickets AS t
    ON a.agent_id = t.assigned_agent_id
ORDER BY a.agent_id, t.ticket_id;
```

> **Key Idea:** `INNER JOIN` answers, “Show me rows that participate in this relationship.”

## `JOIN` and `INNER JOIN`

These keywords are equivalent. Writing `INNER JOIN` while learning can make your intent more obvious.
