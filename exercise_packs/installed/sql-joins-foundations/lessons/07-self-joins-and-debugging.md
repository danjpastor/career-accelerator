# Self Joins and a Reliable Debugging Method

A **self join** uses the same table more than once under different aliases. It is useful when rows relate to other rows in that table.

:::columns
:::column
> **Learning Goals:**
> ✓ Assign role-based aliases to the same table.
> ✓ Preserve top-level rows with no parent.
> ✓ Debug joins by checking keys, grain, and row counts in stages.
:::column
```sql
SELECT
    child.category_name,
    parent.category_name AS parent_category_name
FROM product_categories AS child
LEFT JOIN product_categories AS parent
    ON child.parent_category_id = parent.category_id;
```
:::

## One table, two roles

| Alias | Role |
|---|---|
| `child` | The category row being reported |
| `parent` | The row representing its parent category |

A `LEFT JOIN` preserves top-level categories whose `parent_category_id` is `NULL`.

## A join debugging sequence

### 1. Inspect keys

```sql
SELECT category_id, category_name, parent_category_id
FROM product_categories;
```

### 2. Count source rows

Know how many rows exist before joining.

### 3. Run only the join keys

```sql
SELECT child.category_id, parent.category_id AS parent_id
FROM product_categories AS child
LEFT JOIN product_categories AS parent
    ON child.parent_category_id = parent.category_id;
```

### 4. Check unmatched rows

```sql
WHERE parent.category_id IS NULL
```

### 5. Add calculations last

Do not debug relationships and complex aggregation simultaneously.

> **Final habit:** Explain the query in one sentence: “Preserve ___, match ___ using ___, and expect one output row per ___.”
