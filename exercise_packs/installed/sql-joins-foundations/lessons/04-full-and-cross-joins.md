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
    COALESCE(m.campaign_code, f.campaign_code) AS campaign_code,
    m.marketing_name,
    f.finance_name
FROM marketing_campaigns AS m
FULL OUTER JOIN finance_campaigns AS f
    ON m.campaign_code = f.campaign_code;
```
:::

## FULL OUTER JOIN

A full outer join returns matched rows plus unmatched rows from both systems. `COALESCE` is useful when the shared identifier could come from either side.

| Marketing row | Finance row | Returned? |
|---|---|---|
| Matched | Matched | Yes, combined |
| Present | Missing | Yes, finance columns `NULL` |
| Missing | Present | Yes, marketing columns `NULL` |

## CROSS JOIN

A cross join produces every row combination and has no `ON` condition.

```sql
SELECT
    s.shift_name,
    l.location_name
FROM work_shifts AS s
CROSS JOIN office_locations AS l;
```

If there are 3 shifts and 4 locations, the result has `3 × 4 = 12` rows.

> **Warning:** An accidental missing join condition can multiply rows dramatically. Check expected row counts before trusting totals.
