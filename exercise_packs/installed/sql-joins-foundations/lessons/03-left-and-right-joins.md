# LEFT and RIGHT JOIN: Choose the Preserved Side

An outer join keeps unmatched rows from a chosen side. The most useful question is not “Which diagram do I remember?” It is **Which table must be preserved?**

:::columns
:::column
> **Learning Goals:**
> ✓ Identify the preserved table before writing SQL.
> ✓ Interpret `NULL` values created by unmatched rows.
> ✓ Rewrite a `RIGHT JOIN` as a clearer `LEFT JOIN` when useful.
:::column
```sql
SELECT
    c.customer_name,
    o.order_id
FROM customers AS c
LEFT JOIN orders AS o
    ON c.customer_id = o.customer_id;
```
:::

## LEFT JOIN

`LEFT JOIN` returns every row from the table written on the left. Matching right-side values are added when available. When no match exists, right-side columns become `NULL`.

| Left customer | Matching orders | Output rows |
|---|---:|---:|
| Apex Studios | 2 | 2 |
| Bluebird Games | 1 | 1 |
| Evergreen Health | 0 | 1 row with order columns `NULL` |

## RIGHT JOIN

`RIGHT JOIN` preserves the table written on the right.

```sql
FROM customers AS c
RIGHT JOIN regions AS r
    ON c.region_id = r.region_id
```

You can usually make the same intent easier to read by swapping table order and using `LEFT JOIN`:

```sql
FROM regions AS r
LEFT JOIN customers AS c
    ON r.region_id = c.region_id
```

Both versions preserve every region.

## Find unmatched rows

A common anti-join pattern preserves rows, then keeps only those with no match:

```sql
SELECT
    c.customer_id,
    c.customer_name
FROM customers AS c
LEFT JOIN orders AS o
    ON c.customer_id = o.customer_id
WHERE o.order_id IS NULL;
```

> **Key Idea:** The `NULL` does not necessarily come from the source data. It may be a placeholder created because the outer join found no partner.

## Count matches correctly

To keep zero-match rows, count a column from the optional table—not `COUNT(*)`.

```sql
COUNT(o.order_id) AS order_count
```

For an unmatched customer, `o.order_id` is `NULL`, so the count is zero.
