# Correlated Subqueries

> **Learning goal:** Recognize when an inner query depends on the current outer row and explain that row-by-row relationship.

A correlated subquery refers to the **current row** of the outer query.

```sql
SELECT e.employee_name, e.department_id, e.salary
FROM employees AS e
WHERE e.salary > (
    SELECT AVG(e2.salary)
    FROM employees AS e2
    WHERE e2.department_id = e.department_id
);
```

## What makes it correlated?

The outer alias `e` appears inside the inner query:

```sql
WHERE e2.department_id = e.department_id
                         -- current outer employee
```

The inner calculation therefore depends on whichever employee the outer query is evaluating.

## Row-by-row mental model

For Ana in department 10:

1. Calculate the average salary for department 10.
2. Compare Ana's salary with that average.

For Jordan in department 20:

1. Calculate the average salary for department 20.
2. Compare Jordan's salary with that average.

Conceptually, the benchmark changes with the outer row.

## How to spot correlation

Look for an outer-table alias inside the subquery. If the inner query cannot run by itself because it refers to the outer alias, it is correlated.

## Common uses

- Compare each employee with their department average.
- Check whether each customer has a qualifying order.
- Count related rows for every parent row.
- Find parent rows with no matching child rows.
- Compare a row with other rows in the same group.

## Correlated subquery in SELECT

A scalar correlated subquery can create one calculated column per outer row:

```sql
SELECT
    c.customer_name,
    (
        SELECT COUNT(*)
        FROM orders AS o
        WHERE o.customer_id = c.customer_id
          AND o.status = 'Completed'
    ) AS completed_order_count
FROM customers AS c;
```

The inner `COUNT(*)` returns one value for each current customer.

## Performance and readability

Correlated subqueries can be expressive, but they may be less efficient on large datasets. A join, grouped CTE, or window function may perform better. First understand the logic; then compare alternatives.

### Quick checkpoint

Complete this sentence:

> For each outer row, the inner query calculates or checks __________ using the current row's __________.
