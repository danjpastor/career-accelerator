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
    o.order_id,
    c.customer_name,
    o.total_amount
FROM orders AS o
INNER JOIN customers AS c
    ON o.customer_id = c.customer_id
WHERE o.status = 'Completed';
```
:::

## What is preserved?

With an `INNER JOIN`, neither table is guaranteed to be preserved. A row survives only when a match exists on both sides.

| Situation | Returned by `INNER JOIN`? |
|---|---|
| Customer has a matching order | Yes |
| Customer has no orders | No |
| Order has an unknown customer ID | No |
| Key is `NULL` | No equality match |

## Think in pairs

Suppose customer 1 has two orders. The customer row can match twice, producing two output rows. Joins do not automatically keep one row per customer.

```sql
SELECT
    c.customer_id,
    c.customer_name,
    o.order_id
FROM customers AS c
INNER JOIN orders AS o
    ON c.customer_id = o.customer_id
ORDER BY c.customer_id, o.order_id;
```

> **Key Idea:** `INNER JOIN` answers, “Show me rows that participate in this relationship.” It is ideal when unmatched records should not appear.

## `JOIN` and `INNER JOIN`

These are equivalent:

```sql
FROM customers AS c
JOIN orders AS o
    ON c.customer_id = o.customer_id
```

```sql
FROM customers AS c
INNER JOIN orders AS o
    ON c.customer_id = o.customer_id
```

Writing `INNER JOIN` while learning can make your intent more obvious.
