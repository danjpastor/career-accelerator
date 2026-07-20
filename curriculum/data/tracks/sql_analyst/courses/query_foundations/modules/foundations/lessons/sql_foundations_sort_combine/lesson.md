# Sorting and Combining Foundation Clauses

> **Learning goal:** Produce decision-ready result sets by ordering rows, applying multiple sort keys, and combining `SELECT`, `WHERE`, `ORDER BY`, and `LIMIT` in the correct clause order.

## ORDER BY controls presentation order

A result set has no guaranteed business order unless the query specifies one. `ORDER BY` sorts the returned rows:

```sql
SELECT request_id, submitted_date
FROM purchase_requests
ORDER BY submitted_date ASC;
```

`ASC` means ascending and is the default. For dates, ascending usually means oldest to newest. `DESC` means descending, such as newest to oldest or highest to lowest.

## Sort direction depends on the business question

| Business wording | Typical sort |
|---|---|
| Oldest first | `ORDER BY date_column ASC` |
| Newest first | `ORDER BY date_column DESC` |
| Highest value first | `ORDER BY amount DESC` |
| Alphabetical A–Z | `ORDER BY name ASC` |
| Lowest inventory first | `ORDER BY units_on_hand ASC` |

Do not choose `DESC` merely because it feels more important. Translate the requested order explicitly.

## Multiple sort keys create stable grouping

You can sort by more than one expression:

```sql
SELECT region, account_name, annual_value
FROM customer_accounts
ORDER BY region ASC, annual_value DESC;
```

SQL sorts by `region` first. Within each region, it sorts by `annual_value` from highest to lowest.

A second sort key is useful when the first key has repeated values.

## Clause order is structural

Foundation queries generally follow this sequence:

```sql
SELECT ...
FROM ...
WHERE ...
ORDER BY ...
LIMIT ...;
```

The clauses are not interchangeable. `WHERE` must come before `ORDER BY`, and `LIMIT` normally appears after sorting.

A useful mental model is:

1. Choose the source.
2. Filter eligible rows.
3. Select the output columns.
4. Sort the result.
5. Limit how much is shown.

The written SQL order begins with `SELECT`, but the logical thinking can start with the business population.

## Top-N questions require ORDER BY and LIMIT together

To return the five highest approved requests:

```sql
SELECT request_id, requested_amount
FROM purchase_requests
WHERE approval_status = 'Approved'
ORDER BY requested_amount DESC
LIMIT 5;
```

Without `ORDER BY`, `LIMIT 5` would return an arbitrary preview rather than the top five.

## Worked example 1: oldest unresolved work

A facilities team wants the oldest unresolved inspections:

```sql
SELECT inspection_id, status, due_date
FROM inspections
WHERE status IN ('Open', 'Pending')
ORDER BY due_date ASC;
```

Ascending date order places the oldest records first.

## Worked example 2: category then value

A procurement analyst wants approved requests grouped alphabetically by category and ranked by amount within each category:

```sql
SELECT category, request_id, requested_amount
FROM purchase_requests
WHERE approval_status = 'Approved'
ORDER BY category ASC, requested_amount DESC;
```

The first sort key defines the groups; the second ranks rows inside each group.

## Common mistakes

### Placing ORDER BY before WHERE

This is invalid:

```sql
SELECT request_id
FROM purchase_requests
ORDER BY submitted_date
WHERE status = 'Open';
```

### Limiting before defining the top rows

`LIMIT` without `ORDER BY` does not answer “highest,” “lowest,” “newest,” or “oldest.”

### Sorting in the wrong direction

“Oldest first” requires ascending date order. “Highest first” requires descending numeric order.

### Forgetting a tie-breaker

If several rows share the same first sort value, their relative order may remain unspecified. Add another meaningful key when consistent order matters.

## Build complex queries one clause at a time

1. Start with the requested columns and table.
2. Run the query to confirm the schema.
3. Add the filter and verify the qualifying population.
4. Add sorting and inspect the order.
5. Add the limit last.

This incremental workflow makes errors easier to isolate.

## Lesson recap

- `ORDER BY` is required for a meaningful guaranteed order.
- `ASC` sorts low-to-high, A-to-Z, or oldest-to-newest.
- `DESC` sorts high-to-low, Z-to-A, or newest-to-oldest.
- Multiple sort keys apply from left to right.
- Foundation clause order is `SELECT`, `FROM`, `WHERE`, `ORDER BY`, `LIMIT`.
- Top-N queries combine filtering, sorting, and limiting.
