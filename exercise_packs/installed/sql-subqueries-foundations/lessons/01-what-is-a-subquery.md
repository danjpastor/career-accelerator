# What Is a Subquery?

A **subquery** is a complete SQL query placed inside another SQL query. It lets you solve a larger question by calculating a smaller result first.

:::columns
:::column
> **Learning Goals:**
> ✓ Recognize the inner and outer query.
> ✓ Predict whether the inner query returns one value, a list, or a table.
> ✓ Explain how the outer query consumes that result.
:::column
```sql
SELECT product_name, unit_price
FROM products
WHERE unit_price > (
    SELECT AVG(unit_price)
    FROM products
);
```
:::

:::columns
:::column
## Example Result

| product_name | unit_price |
|---|---:|
| Studio Monitor | 349.00 |
| Color Panel | 799.00 |
| Reference Display | 1299.00 |
:::column
> **Key Idea:** The inner query calculates one benchmark—the average product price. The outer query uses that benchmark to filter product rows.
:::

## The two questions inside the example

### 1. Smaller question: What is the average product price?

```sql
SELECT AVG(unit_price)
FROM products;
```

This returns **one row and one column**.

### 2. Larger question: Which products cost more than that value?

```sql
SELECT product_name, unit_price
FROM products
WHERE unit_price > (...);
```

The outer query treats the inner result like a value written after `>`.

## The three result shapes

| Inner result shape | Example | Common outer use |
|---|---|---|
| One value | One average price | `=`, `>`, `<`, `>=`, `<=` |
| One column with many values | A list of product IDs | `IN` or `NOT IN` |
| A table | One summary row per store | Put it in `FROM` and give it an alias |

`EXISTS` and `NOT EXISTS` are slightly different: they ask only whether the inner search returns any rows.

## Read from the inside outward

1. What question does the innermost query answer?
2. What columns and rows does it return?
3. Where is that result inserted into the next query?
4. What does the outer query do with it?

Use these two sentences throughout the pack:

- **The inner query returns...**
- **The outer query uses that result to...**

> **First survival rule:** Run the inner query by itself before nesting it. If you cannot explain its output, do not build the outer query yet.

### Quick checkpoint

For the product example, complete these sentences:

- The inner query returns **one value: the average unit price**.
- The outer query uses it to **keep products whose price is greater than that value**.
