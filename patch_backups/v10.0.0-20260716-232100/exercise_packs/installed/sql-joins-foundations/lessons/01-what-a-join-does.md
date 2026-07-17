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
    c.customer_name,
    r.region_name
FROM customers AS c
INNER JOIN regions AS r
    ON c.region_id = r.region_id;
```
:::

:::columns
:::column
## Example Result

| customer_name | region_name |
|---|---|
| Apex Studios | East |
| Bluebird Games | West |
| Cascade Media | East |
| Delta Retail | Central |
| Frostline Labs | West |
:::column
> **Key Idea:** The join condition compares `customers.region_id` with `regions.region_id`. Evergreen Health has no region key, so an `INNER JOIN` does not return it.
:::

## Start with table grain

**Grain** means what one row represents.

| Table | One row represents | Likely key |
|---|---|---|
| `customers` | One customer | `customer_id` |
| `regions` | One region | `region_id` |
| `orders` | One order | `order_id` |
| `order_items` | One product line on one order | `order_item_id` |

If you cannot state the grain, it is hard to predict the number of rows after a join.

## The four questions to ask

1. What does one row represent in the first table?
2. What does one row represent in the second table?
3. Which columns describe their relationship?
4. Can one row match zero, one, or many rows on the other side?

## A join condition is not a filter condition

The `ON` clause explains **how the tables relate**.

```sql
ON c.customer_id = o.customer_id
```

A `WHERE` clause usually filters the already joined result.

```sql
WHERE o.status = 'Completed'
```

Keeping those jobs separate makes joins much easier to read.

> **First survival rule:** Before running a join, predict whether each row on the preserved side can produce zero, one, or many output rows.
