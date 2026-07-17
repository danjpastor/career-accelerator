# One-Value Subqueries

> **Learning goal:** Build scalar subqueries that calculate one benchmark and use it in a normal comparison.

A scalar subquery returns exactly **one row and one column**.

Examples of one-value calculations include:

```sql
SELECT AVG(resolution_minutes) FROM support_tickets;
SELECT MAX(stock_on_hand) FROM inventory;
SELECT COUNT(*) FROM active_campaigns;
```

Because each result behaves like one value, the outer query can compare against it. This example finds email tickets that took longer than the average email-ticket resolution time:

```sql
SELECT ticket_id, resolution_minutes
FROM support_tickets
WHERE channel = 'Email'
  AND resolution_minutes > (
      SELECT AVG(resolution_minutes)
      FROM support_tickets
      WHERE channel = 'Email'
  );
```

## A reliable five-step process

1. Write the smaller calculation by itself.
2. Run it and confirm that it returns one value.
3. Place parentheses around it.
4. Insert it where a normal value could appear.
5. Run the complete query and explain both stages.

## The result-shape contract

After an operator such as `>`, SQL expects one value:

```sql
WHERE resolution_minutes > (one value here)
```

This creates a shape mismatch:

```sql
WHERE resolution_minutes > (
    SELECT resolution_minutes
    FROM support_tickets
)
```

The inner query may return many rows. Aggregate functions such as `AVG`, `MIN`, `MAX`, and `COUNT` commonly reduce many rows into one value.

## Filters do not automatically carry inward

The outer filter chooses the rows to return. The inner filter defines the benchmark. When a benchmark applies only to one category, repeat that category condition inside the subquery.

## Common mistakes

- Returning many rows where one value is expected.
- Calculating the wrong benchmark because an inner filter is missing.
- Adding `GROUP BY` when one overall value is required.
- Rounding the benchmark before comparison when exact precision is preferable.

### Quick checkpoint

Before nesting a scalar query, say:

> This query returns one value: __________.
