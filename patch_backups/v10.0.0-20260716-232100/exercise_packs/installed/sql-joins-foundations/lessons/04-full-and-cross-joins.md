# FULL OUTER and CROSS JOIN

These joins solve very different problems. `FULL OUTER JOIN` preserves both sides. `CROSS JOIN` deliberately creates every possible combination.

:::columns
:::column
> **Learning Goals:**
> ✓ Reconcile two systems while retaining unmatched records from both.
> ✓ Recognize the rapid row growth of a Cartesian product.
> ✓ Choose these specialized joins intentionally.
:::column
```sql
SELECT
    COALESCE(c.account_id, b.account_id) AS account_id,
    c.account_name,
    b.billing_name
FROM crm_accounts AS c
FULL OUTER JOIN billing_accounts AS b
    ON c.account_id = b.account_id;
```
:::

## FULL OUTER JOIN

A full outer join returns:

- Matched rows from both tables
- Left-only rows with right-side columns as `NULL`
- Right-only rows with left-side columns as `NULL`

| CRM row | Billing row | Returned? |
|---|---|---|
| Matched | Matched | Yes, combined |
| Present | Missing | Yes, billing columns `NULL` |
| Missing | Present | Yes, CRM columns `NULL` |

`COALESCE` is useful when the shared identifier could come from either side.

## CROSS JOIN

A cross join does not use an `ON` condition. It produces every row combination.

```sql
SELECT
    r.region_name,
    p.product_name
FROM regions AS r
CROSS JOIN products AS p;
```

If there are 4 regions and 4 products, the result has `4 × 4 = 16` rows.

## Common uses

| Join | Useful for |
|---|---|
| `FULL OUTER JOIN` | Reconciliation, migration audits, identifying missing records across systems |
| `CROSS JOIN` | Scenario grids, calendars, every product-region combination, test matrices |

> **Warning:** An accidental missing `ON` condition can behave like a cross join and multiply rows dramatically. Check expected row counts before trusting totals.
