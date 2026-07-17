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
    i.invoice_id,
    COUNT(il.invoice_line_id) AS line_count,
    SUM(il.quantity * il.unit_price) AS calculated_total
FROM invoices AS i
INNER JOIN invoice_lines AS il
    ON i.invoice_id = il.invoice_id
GROUP BY i.invoice_id;
```
:::

## How fanout happens

One invoice with three lines produces three joined rows. A stored invoice total would repeat on each line.

This is dangerous after the join:

```sql
SUM(i.invoice_total)
```

It can add the same higher-grain value multiple times.

## Safer strategies

- Sum line-level values such as `quantity * unit_price`.
- Aggregate detail rows to one row per invoice before joining elsewhere.
- Use `COUNT(DISTINCT i.invoice_id)` when the question asks for invoices, not lines.
- State the intended output grain before writing the query.

> **Key Idea:** Duplicate-looking rows are often legitimate matches. The error occurs when you aggregate a repeated higher-grain value as though each copy were unique.
