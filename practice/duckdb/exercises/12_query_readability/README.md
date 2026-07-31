# DuckDB Exercise 13: Refactor an unreadable analytics query

**Week:** 4
**Estimated time:** 30 minutes  
**Concepts:** CTEs, aliases, formatting, validation

## Scenario

A campaign-performance query returns the right numbers but is difficult for another analyst to review. Refactor it without changing the business result.

## Tables

- `ex12_campaign_performance`

## Source CSV files

- `campaign_performance.csv`

## Starting query

Refactor this query inside the SQL editor. The query is intentionally compressed so its logic is difficult to review.

```sql
SELECT campaign_channel, SUM(spend), SUM(revenue), SUM(revenue) - SUM(spend), ROUND(SUM(revenue) / NULLIF(SUM(spend), 0), 4)
FROM ex12_campaign_performance
WHERE campaign_date >= '2026-06-01'
GROUP BY campaign_channel
HAVING SUM(spend) > 500
ORDER BY 5 DESC;
```

## Tasks

### Task 1

Refactor the starting campaign query shown in the exercise guide without changing its result. Return `campaign_channel`, `spend`, `revenue`, `profit`, and `return_on_spend`, with return on spend rounded to four decimal places.

**Result requirements**

- Return columns in this order: `campaign_channel`, `spend`, `revenue`, `profit`, `return_on_spend`.
- Return 4 rows.
- Round the requested result to 4 decimal places.

### Task 2

Rewrite the starting query with each major SQL clause on its own line and consistent indentation. Then return the number of source rows as `formatted_rows`.

**Result requirements**

- Return columns in this order: `formatted_rows`.
- Return 1 row.

### Task 3

Build the channel report so it sorts by the `return_on_spend` alias instead of column position 5. Then return the number of distinct channels as `channel_count`.

**Result requirements**

- Return columns in this order: `channel_count`.
- Return 1 row.

### Task 4

Move channel aggregation into a clearly named CTE. Return total `total_spend` and `total_revenue`, each rounded to two decimal places.

**Result requirements**

- Return columns in this order: `total_spend`, `total_revenue`.
- Return 1 row.
- Round the requested result to 2 decimal places.

### Task 5

Add short SQL comments that explain the channel-summary CTE and its final filter. Return `campaign_channel` and `profit` for the four report rows.

**Result requirements**

- Return columns in this order: `campaign_channel`, `profit`.
- Return 4 rows.

### Task 6

Confirm the refactored query still covers every source row. Return the matching row count as `matching_rows`.

**Result requirements**

- Return columns in this order: `matching_rows`.
- Return 1 row.

### Task 7

Write two SQL-comment sentences explaining how readable SQL reduces analytics risk, then return the source row count as `reviewed_rows`.

**Result requirements**

- Return columns in this order: `reviewed_rows`.
- Return 1 row.

## Complete the exercise

1. Complete each task in the SQL editor.
2. Use **Check Task** for specific feedback and hints.
3. Use **Check Exercise** after every task passes.
4. Select **Submit Exercise** to record completion.

