# LEFT and RIGHT JOIN: Choose the Preserved Side

An outer join keeps unmatched rows from a chosen side. The most useful question is **Which table must be preserved?**

:::columns
:::column
> **Learning Goals:**
> ✓ Identify the preserved table before writing SQL.
> ✓ Interpret `NULL` values created by unmatched rows.
> ✓ Rewrite a `RIGHT JOIN` as a clearer `LEFT JOIN` when useful.
:::column
```sql
SELECT
    p.project_name,
    t.task_id
FROM projects AS p
LEFT JOIN project_tasks AS t
    ON p.project_id = t.project_id;
```
:::

## LEFT JOIN

`LEFT JOIN` returns every row from the table written on the left. Matching right-side values are added when available. When no match exists, right-side columns become `NULL`.

| Left project | Matching tasks | Output rows |
|---|---:|---:|
| Website Refresh | 3 | 3 |
| Mobile Launch | 1 | 1 |
| Archive Cleanup | 0 | 1 row with task columns `NULL` |

## RIGHT JOIN

`RIGHT JOIN` preserves the table written on the right.

```sql
FROM project_tasks AS t
RIGHT JOIN projects AS p
    ON t.project_id = p.project_id
```

The same intent is often easier to read by swapping table order and using `LEFT JOIN`.

## Find unmatched rows

```sql
SELECT p.project_id, p.project_name
FROM projects AS p
LEFT JOIN project_tasks AS t
    ON p.project_id = t.project_id
WHERE t.task_id IS NULL;
```

## Count matches correctly

To preserve zero-match rows, count a column from the optional table—not `COUNT(*)`.

```sql
COUNT(t.task_id) AS task_count
```

> **Key Idea:** A `NULL` in the result may be a placeholder created because the outer join found no partner.
