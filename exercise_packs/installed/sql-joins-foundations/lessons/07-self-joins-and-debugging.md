# Self Joins and a Reliable Debugging Method

A **self join** uses the same table more than once under different aliases. It is useful when rows relate to other rows in that table, such as employees and managers.

:::columns
:::column
> **Learning Goals:**
> ✓ Assign role-based aliases to the same table.
> ✓ Preserve top-level rows with no parent.
> ✓ Debug joins by checking keys, grain, and row counts in stages.
:::column
```sql
SELECT
    e.employee_name,
    m.employee_name AS manager_name
FROM employees AS e
LEFT JOIN employees AS m
    ON e.manager_id = m.employee_id;
```
:::

## One table, two roles

| Alias | Role |
|---|---|
| `e` | The employee row being reported |
| `m` | The row representing that employee’s manager |

A `LEFT JOIN` preserves employees whose `manager_id` is `NULL`, such as company leaders.

## A join debugging sequence

### 1. Inspect keys

```sql
SELECT customer_id, customer_name
FROM customers;
```

```sql
SELECT order_id, customer_id
FROM orders;
```

### 2. Count source rows

Know how many rows exist before joining.

### 3. Run only the join keys

```sql
SELECT
    c.customer_id,
    o.order_id
FROM customers AS c
LEFT JOIN orders AS o
    ON c.customer_id = o.customer_id;
```

### 4. Check unmatched rows

```sql
WHERE o.order_id IS NULL
```

### 5. Add calculations last

Do not debug relationships and complex aggregation simultaneously.

## Join choice summary

| Need | Join to consider |
|---|---|
| Only matched records | `INNER JOIN` |
| Keep all rows from the primary table | `LEFT JOIN` |
| Keep all rows from the table written on the right | `RIGHT JOIN`, or swap order and use `LEFT JOIN` |
| Keep unmatched rows from both systems | `FULL OUTER JOIN` |
| Generate every combination | `CROSS JOIN` |
| Relate rows within one table | Self join with two aliases |

> **Final habit:** Explain the query in one sentence: “Preserve ___, match ___ using ___, and expect one output row per ___.”
