# Subquery vs. Join vs. CTE

> **Learning goal:** Choose a clear SQL structure based on the question instead of assuming every multi-step problem must use a subquery.

The same analytical question can often be answered in several valid ways. The goal is not to force every question into a subquery. The goal is to understand what each tool expresses clearly.

## Example question

> Which customers have at least one completed order?

### IN subquery

```sql
SELECT customer_id, customer_name
FROM customers
WHERE customer_id IN (
    SELECT customer_id
    FROM orders
    WHERE status = 'Completed'
);
```

This emphasizes a **list of qualifying customer IDs**.

### EXISTS subquery

```sql
SELECT c.customer_id, c.customer_name
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.customer_id
      AND o.status = 'Completed'
);
```

This emphasizes **whether a related row exists**.

### JOIN

```sql
SELECT DISTINCT c.customer_id, c.customer_name
FROM customers AS c
JOIN orders AS o
    ON o.customer_id = c.customer_id
WHERE o.status = 'Completed';
```

This directly combines rows from both tables. `DISTINCT` is needed because one customer can match several completed orders.

## Practical decision guide

| Need | Often clear with |
|---|---|
| Compare with one calculated benchmark | Scalar subquery |
| Match a returned list | `IN` subquery |
| Test whether related rows exist | `EXISTS` / `NOT EXISTS` |
| Return columns from multiple tables | `JOIN` |
| Break a long query into named stages | CTE |
| Reuse a summarized result | CTE or joined derived table |

## CTEs are named query stages

A CTE can make a nested query easier to read:

```sql
WITH customer_totals AS (
    SELECT customer_id, SUM(amount) AS total_spent
    FROM orders
    WHERE status = 'Completed'
    GROUP BY customer_id
)
SELECT customer_id, total_spent
FROM customer_totals
WHERE total_spent > 1000;
```

The CTE is not “more advanced magic.” It simply names a query stage before the final `SELECT`.

## A useful rule of thumb

- Start with the form that makes the question easiest to explain.
- Verify correctness on small data.
- Compare alternatives when readability or performance matters.

Do not treat joins, subqueries, and CTEs as competing topics. They are related tools for organizing multi-table and multi-step logic.

### Quick checkpoint

If you need columns from both `customers` and `orders`, a `JOIN` may be natural. If you only need to know whether an order exists, `EXISTS` may communicate the intent more directly.
