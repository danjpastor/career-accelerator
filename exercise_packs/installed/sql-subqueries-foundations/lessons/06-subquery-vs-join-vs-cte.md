# Subquery vs. Join vs. CTE

> **Learning goal:** Choose a clear SQL structure based on the question instead of assuming every multi-step problem must use a subquery.

The same analytical question can often be answered in several valid ways.

## Example question

> Which stores have at least one low-stock alert?

### IN subquery

```sql
SELECT store_id, store_name
FROM stores
WHERE store_id IN (
    SELECT store_id
    FROM inventory_alerts
    WHERE alert_type = 'Low Stock'
);
```

### EXISTS subquery

```sql
SELECT s.store_id, s.store_name
FROM stores AS s
WHERE EXISTS (
    SELECT 1
    FROM inventory_alerts AS a
    WHERE a.store_id = s.store_id
      AND a.alert_type = 'Low Stock'
);
```

### JOIN

```sql
SELECT DISTINCT s.store_id, s.store_name
FROM stores AS s
JOIN inventory_alerts AS a
    ON a.store_id = s.store_id
WHERE a.alert_type = 'Low Stock';
```

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

```sql
WITH campaign_totals AS (
    SELECT campaign_id, SUM(clicks) AS total_clicks
    FROM daily_campaign_metrics
    GROUP BY campaign_id
)
SELECT campaign_id, total_clicks
FROM campaign_totals
WHERE total_clicks > 10000;
```

Start with the form that makes the question easiest to explain, verify it on small data, and compare alternatives when readability or performance matters.
