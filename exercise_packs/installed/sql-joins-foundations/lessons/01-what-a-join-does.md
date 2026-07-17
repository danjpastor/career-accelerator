# What a Join Actually Does

A **join** combines rows from two tables by testing a relationship between them. SQL does not place rows together because they are on the same line or look similar. It evaluates the `ON` condition for possible row pairs.

:::columns
:::column
> **Learning Goals:**
> ✓ Identify the grain of each table.
> ✓ Find the columns that represent the relationship.
> ✓ Predict whether one row can match zero, one, or many rows.
:::column
```sql
SELECT
    p.project_name,
    c.client_name
FROM projects AS p
INNER JOIN clients AS c
    ON p.client_id = c.client_id;
```
:::

:::columns
:::column
## Example Result

| project_name | client_name |
|---|---|
| Website Refresh | Northwind Studio |
| Mobile Launch | Harbor Media |
| Reporting Upgrade | Northwind Studio |
:::column
> **Key Idea:** The join condition compares the client key stored on each project with the client table's primary key. A project with no matching client does not survive an `INNER JOIN`.
:::

## Start with table grain

**Grain** means what one row represents.

| Table | One row represents | Likely key |
|---|---|---|
| `projects` | One project | `project_id` |
| `clients` | One client | `client_id` |
| `tasks` | One task | `task_id` |
| `time_entries` | One time entry | `time_entry_id` |

## The four questions to ask

1. What does one row represent in the first table?
2. What does one row represent in the second table?
3. Which columns describe their relationship?
4. Can one row match zero, one, or many rows on the other side?

## A join condition is not a filter condition

The `ON` clause explains **how the tables relate**.

```sql
ON p.client_id = c.client_id
```

A `WHERE` clause filters the joined result.

```sql
WHERE p.status = 'Active'
```

> **First survival rule:** Before running a join, predict whether each row on the preserved side can produce zero, one, or many output rows.
