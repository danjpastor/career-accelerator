# Join Grain, Duplicates, and Fanout

A join can be logically correct and still produce the wrong total. The most common cause is **fanout**: one row from a higher-level table matches several detail rows.

:::columns
:::column
> **Learning Goals:**
> ✓ Predict output grain after a one-to-many join.
> ✓ Recognize when a total is repeated across detail rows.
> ✓ Aggregate at the correct level before or after joining.
:::column
```sql
SELECT
    o.order_id,
    COUNT(oi.order_item_id) AS line_count,
    SUM(oi.quantity * oi.unit_price) AS calculated_total
FROM orders AS o
INNER JOIN order_items AS oi
    ON o.order_id = oi.order_id
GROUP BY o.order_id;
```
:::

## How fanout happens

Order 1001 has two line items. After joining `orders` to `order_items`, the order row appears twice—once per line.

| order_id | stored order total | line item |
|---:|---:|---|
| 1001 | 1200 | Render Credits |
| 1001 | 1200 | Storage Bundle |

This is dangerous:

```sql
SUM(o.total_amount)
```

For order 1001, it would add `1200 + 1200` and overstate revenue.

## Safer strategies

- Sum line-level values such as `quantity * unit_price`.
- Aggregate detail rows to one row per order before joining elsewhere.
- Use `COUNT(DISTINCT o.order_id)` when the question asks for orders, not lines.
- State the intended output grain in plain language before writing the query.

## Grain checklist

| Question | Example answer |
|---|---|
| What should one output row represent? | One order |
| Which table is more detailed? | `order_items` |
| Can one order match many lines? | Yes |
| Which value repeats after the join? | `orders.total_amount` |

> **Key Idea:** Duplicate-looking rows are often legitimate matches. The error occurs when you aggregate a repeated higher-grain value as though each copy were unique.
