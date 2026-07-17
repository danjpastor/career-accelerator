# Multiple Values, IN, EXISTS, and NOT EXISTS

> **Learning goal:** Choose between a returned list (`IN`) and a yes-or-no relationship test (`EXISTS` or `NOT EXISTS`).

Sometimes the smaller query returns one column containing several values.

| `agent_id` |
|---:|
| 2 |
| 4 |
| 7 |

A normal `=` comparison expects one value, so use `IN` when the outer value should match any value in the list.

```sql
SELECT agent_id, agent_name
FROM support_agents
WHERE agent_id IN (
    SELECT assigned_agent_id
    FROM support_tickets
    WHERE priority = 'Critical'
);
```

Read it as: keep agents whose ID appears in the list of agents assigned to critical tickets.

## EXISTS asks a yes-or-no question

```sql
SELECT a.agent_id, a.agent_name
FROM support_agents AS a
WHERE EXISTS (
    SELECT 1
    FROM support_tickets AS t
    WHERE t.assigned_agent_id = a.agent_id
      AND t.priority = 'Critical'
);
```

For each agent, the inner query asks whether at least one qualifying related row exists.

## NOT EXISTS finds missing relationships

```sql
SELECT a.agent_id, a.agent_name
FROM support_agents AS a
WHERE NOT EXISTS (
    SELECT 1
    FROM support_tickets AS t
    WHERE t.assigned_agent_id = a.agent_id
      AND t.priority = 'Critical'
);
```

This keeps agents for whom the related search finds zero critical tickets.

## Which one should you use?

| Your mental question | Helpful pattern |
|---|---|
| Is this value in a returned list? | `IN` |
| Does at least one related row exist? | `EXISTS` |
| Are there zero related rows? | `NOT EXISTS` |

`NOT EXISTS` is usually easier to reason about than `NOT IN` when null values might appear in the inner result.
