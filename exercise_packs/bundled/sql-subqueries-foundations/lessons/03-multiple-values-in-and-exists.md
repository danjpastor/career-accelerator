# Multiple Values, IN, EXISTS, and NOT EXISTS

> **Learning goal:** Choose between a returned list (`IN`) and a yes-or-no relationship test (`EXISTS` or `NOT EXISTS`).

Sometimes the smaller query returns one column containing several values.

| `customer_id` |
|---:|
| 1 |
| 3 |
| 5 |
| 7 |

A normal `=` comparison expects one value, so use `IN` when the outer value should match any value in the list.

```sql
SELECT customer_id, customer_name
FROM customers
WHERE customer_id IN (
    SELECT customer_id
    FROM orders
    WHERE status = 'Completed'
);
```

Read it as:

> Keep customers whose ID is in the list of customer IDs from completed orders.

## Duplicates do not change membership

A customer with three completed orders may appear three times in the inner list. The outer `IN` test still asks only whether the ID is present. `DISTINCT` is optional for correctness here, but it can make the inner result easier to inspect.

## EXISTS asks a yes-or-no question

`EXISTS` does not use the returned values. It asks whether the related search finds at least one row.

```sql
SELECT c.customer_id, c.customer_name
FROM customers AS c
WHERE EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.customer_id
      AND o.status = 'Completed'
);
```

For each customer, the inner query asks:

> Is there at least one completed order with this customer's ID?

`SELECT 1` is conventional because `EXISTS` cares only whether a row exists.

## NOT EXISTS finds missing relationships

```sql
SELECT c.customer_id, c.customer_name
FROM customers AS c
WHERE NOT EXISTS (
    SELECT 1
    FROM orders AS o
    WHERE o.customer_id = c.customer_id
      AND o.status = 'Completed'
);
```

Read it as:

> Keep the customer when the related search finds zero completed orders.

This pattern is useful for customers without purchases, employees without assignments, products without sales, or tickets without a response.

## Which one should you use?

| Your mental question | Helpful pattern |
|---|---|
| Is this value in a returned list? | `IN` |
| Does at least one related row exist? | `EXISTS` |
| Are there zero related rows? | `NOT EXISTS` |

`NOT EXISTS` is usually easier to reason about than `NOT IN` when null values might appear in the inner result.

### Quick checkpoint

- `IN` consumes **one column of values**.
- `EXISTS` consumes **only the fact that at least one row was found**.
