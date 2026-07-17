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
    o.order_id,
    c.customer_name,
    p.product_name,
    oi.quantity
FROM orders AS o
INNER JOIN customers AS c
    ON o.customer_id = c.customer_id
INNER JOIN order_items AS oi
    ON o.order_id = oi.order_id
INNER JOIN products AS p
    ON oi.product_id = p.product_id;
```
:::

## Read the relationship chain

```text
customers → orders → order_items → products
```

Each arrow represents a different key comparison:

| Relationship | Join condition |
|---|---|
| Customer to order | `c.customer_id = o.customer_id` |
| Order to line item | `o.order_id = oi.order_id` |
| Line item to product | `oi.product_id = p.product_id` |

## Add one join at a time

1. Join two tables.
2. Run the query and inspect row count and sample rows.
3. Add the next table.
4. Recheck the grain.
5. Add filters only after the relationship is correct.

## Alias preferences

Use short, recognizable aliases:

| Table | Good alias |
|---|---|
| `customers` | `c` |
| `orders` | `o` |
| `order_items` | `oi` |
| `products` | `p` |

Avoid aliases that are so cryptic that they hide the model.

> **Key Idea:** Every added one-to-many relationship can multiply rows. The final result’s grain is determined by the most detailed table selected—often `order_items` in an order analysis.
