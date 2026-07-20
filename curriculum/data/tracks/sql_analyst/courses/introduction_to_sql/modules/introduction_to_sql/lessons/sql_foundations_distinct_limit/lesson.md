# DISTINCT and LIMIT

> **Learning goal:** Explore a dataset safely by returning unique values and controlling how many rows a query produces.

## Duplicate rows can be meaningful

A column often repeats because many records share the same category. The `region` value `West` may appear on several orders. Those rows are not necessarily duplicate source records; they are different orders with the same region.

`DISTINCT` removes duplicate combinations from the **result**:

```sql
SELECT DISTINCT region
FROM sales_orders;
```

The source table is unchanged. The result contains one row for each different `region` value.

## DISTINCT applies to the complete selected combination

With one selected column, uniqueness is easy to interpret. With multiple selected columns, SQL keeps each unique combination:

```sql
SELECT DISTINCT region, sales_channel
FROM sales_orders;
```

If `West` appears with both `Online` and `Retail`, the result contains two rows. `DISTINCT` does not make only the first column unique.

## Use unique-value checks during data exploration

Analysts commonly use `DISTINCT` to:

- Discover available status or category values.
- Detect inconsistent labels such as `Open`, `OPEN`, and `open`.
- Confirm whether a field contains unexpected values.
- Prepare a list for a filter or validation rule.

A unique-value query is often one of the first checks performed on a new categorical column.

## LIMIT controls result size

`LIMIT` caps the number of returned rows:

```sql
SELECT shipment_id, shipped_date
FROM warehouse_shipments
LIMIT 10;
```

This is useful for previewing a table, testing syntax, or inspecting the shape of a result before running a larger query.

## LIMIT does not define which rows are important

Without `ORDER BY`, a database is not required to return rows in a meaningful business order. `LIMIT 5` means “return no more than five rows,” not “return the newest five” or “return the highest five.” Sorting is introduced in a later lesson.

## DISTINCT and LIMIT can work together

```sql
SELECT DISTINCT carrier_name
FROM warehouse_shipments
LIMIT 4;
```

SQL first produces the selected distinct values and then limits how many are returned. This is a quick way to preview a categorical field.

## Worked example 1: inspect available categories

A procurement analyst wants to see the different request types in `purchase_requests`:

```sql
SELECT DISTINCT request_type
FROM purchase_requests;
```

This checks the domain of the field without returning every request.

## Worked example 2: preview a result

A clinic analyst wants a small sample of appointment identifiers and dates:

```sql
SELECT appointment_id, appointment_date
FROM clinic_appointments
LIMIT 6;
```

The query is intentionally a preview, not a ranking.

## Common mistakes

### Expecting DISTINCT to change the source table

`DISTINCT` changes only the query result. Repeated values remain in the original data.

### Assuming multiple selected columns are independently unique

`SELECT DISTINCT region, status` returns unique pairs. A region can still appear more than once if it has multiple statuses.

### Using LIMIT as a business rule

A limited preview is not automatically a representative sample. Do not generalize from five rows unless the sampling method supports that conclusion.

### Mismatching the requested limit

A query that asks for four rows must use `LIMIT 4`, not a memorized value from another exercise.

## Lesson recap

- `DISTINCT` removes repeated result combinations.
- With multiple columns, uniqueness applies to the full combination.
- `LIMIT` caps result size and is useful for exploration.
- `LIMIT` alone does not guarantee which rows appear.
- Neither clause modifies the source table.
