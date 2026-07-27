# Transforming DataFrames

A pandas **DataFrame** is a table with named rows and columns. Transforming a DataFrame often means creating a new column from existing fields, renaming columns, changing types, or replacing inconsistent values.

## Main idea

A pandas **DataFrame** is a table with named rows and columns. Transforming a DataFrame often means creating a new column from existing fields, renaming columns, changing types, or replacing inconsistent values.

When you want to keep the source unchanged, make a copy before editing:

```python
clean_data = raw_data.copy()
clean_data["total"] = clean_data["quantity"] * clean_data["price"]
```

A calculated column should come from the source fields rather than a manually typed final answer. That keeps the analysis repeatable when new rows arrive.

## Example

A shipping analyst copies a packages DataFrame and adds `weight_kg` from a pounds field. They verify a few rows and confirm the original table did not change. The graded exercise creates order calculations and review flags.
