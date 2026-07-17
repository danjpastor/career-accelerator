# Correlated Subqueries

> **Learning goal:** Recognize when an inner query depends on the current outer row and explain that row-by-row relationship.

A correlated subquery refers to the **current row** of the outer query. This example compares each product with the average price in its own category.

```sql
SELECT p.product_name, p.category_id, p.unit_price
FROM products AS p
WHERE p.unit_price > (
    SELECT AVG(p2.unit_price)
    FROM products AS p2
    WHERE p2.category_id = p.category_id
);
```

## What makes it correlated?

The outer alias `p` appears inside the inner query:

```sql
WHERE p2.category_id = p.category_id
                       -- current outer product
```

The benchmark changes with the outer row.

## Row-by-row mental model

For a product in category 10:

1. Calculate the average price for category 10.
2. Compare the current product's price with that average.

For a product in category 20, repeat the process using category 20.

## Correlated subquery in SELECT

A scalar correlated subquery can create one calculated column per outer row:

```sql
SELECT
    project_name,
    (
        SELECT COUNT(*)
        FROM project_tasks AS t
        WHERE t.project_id = p.project_id
          AND t.status = 'Done'
    ) AS completed_task_count
FROM projects AS p;
```

## How to spot correlation

Look for an outer-table alias inside the subquery. If the inner query cannot run by itself because it refers to the outer alias, it is correlated.

Correlated subqueries can be expressive, but a grouped join, CTE, or window function may be more efficient on large data.
