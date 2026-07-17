# Subqueries in the FROM Clause

> **Learning goal:** Treat a summarized inner query as a temporary table that the outer query can filter, join, or calculate from.

A subquery in `FROM` produces a temporary result table for the outer query. This example summarizes campaign revenue by week, then keeps only strong weeks.

```sql
SELECT campaign_week, weekly_revenue
FROM (
    SELECT
        campaign_week,
        SUM(revenue) AS weekly_revenue
    FROM campaign_events
    GROUP BY campaign_week
) AS weekly_summary
WHERE weekly_revenue > 5000;
```

## Stage 1: Build a summary table

```sql
SELECT
    campaign_week,
    SUM(revenue) AS weekly_revenue
FROM campaign_events
GROUP BY campaign_week;
```

One row now represents one campaign week.

## Stage 2: Query that summary

```sql
SELECT campaign_week, weekly_revenue
FROM weekly_summary
WHERE weekly_revenue > 5000;
```

The actual SQL nests stage 1 inside `FROM` instead of creating a permanent table.

## Give every FROM subquery an alias

```sql
) AS weekly_summary
```

The alias names the temporary result and makes its role clear.

## Why not always use HAVING?

Some aggregate filters can be written directly with `HAVING`. A `FROM` subquery is especially helpful when the summary feeds another calculation, receives more filters, or will later be joined to another table.

## Think in tables

For a `FROM` subquery, ask:

- What are the temporary table's columns?
- How many rows does it contain?
- What does one row represent?
