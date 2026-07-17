# Subqueries in the FROM Clause

> **Learning goal:** Treat a summarized inner query as a temporary table that the outer query can filter, join, or calculate from.

A subquery in `FROM` produces a temporary result table for the outer query.

```sql
SELECT department_id, avg_salary
FROM (
    SELECT department_id, AVG(salary) AS avg_salary
    FROM employees
    GROUP BY department_id
) AS department_summary
WHERE avg_salary > 80000;
```

## Stage 1: Build a summary table

```sql
SELECT department_id, AVG(salary) AS avg_salary
FROM employees
GROUP BY department_id;
```

This creates one row per department.

| `department_id` | `avg_salary` |
|---:|---:|
| 10 | 77000.00 |
| 20 | 64333.33 |
| 30 | 96333.33 |
| 40 | 67333.33 |

## Stage 2: Query that summary

The outer query treats the result as if it were a table named `department_summary`:

```sql
SELECT department_id, avg_salary
FROM department_summary
WHERE avg_salary > 80000;
```

The actual SQL nests stage 1 inside `FROM` instead of creating a permanent table.

## Give every FROM subquery an alias

```sql
) AS department_summary
```

The alias names the temporary result and makes its role clear.

## Why not always use HAVING?

Some aggregate filters can be written more directly:

```sql
SELECT department_id, AVG(salary) AS avg_salary
FROM employees
GROUP BY department_id
HAVING AVG(salary) > 80000;
```

That is valid. A `FROM` subquery is especially helpful when:

- The summary will feed another calculation.
- The outer query needs more filters or joins.
- Separating stages makes the logic easier to inspect.
- You are preparing to rewrite the stages as a CTE.

## Think in tables

For a `FROM` subquery, ask:

- What are the temporary table's columns?
- How many rows does it contain?
- What does one row represent?

### Quick checkpoint

In the example, the inner query returns **a four-row department summary table**. The outer query keeps **only summary rows whose average salary exceeds 80,000**.
