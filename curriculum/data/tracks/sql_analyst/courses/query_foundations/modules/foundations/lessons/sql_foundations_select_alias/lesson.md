# Selecting Columns and Using Aliases

> **Learning goal:** Build clear result sets by choosing only the columns a business question needs and giving those columns readable result names with aliases.

## Projection: choosing the shape of the result

In relational language, selecting columns is called **projection**. A table may contain many fields, but most questions need only a subset. Returning fewer columns makes the result easier to inspect, reduces clutter, and communicates the exact purpose of the query.

```sql
SELECT customer_id, signup_date, plan_name
FROM customer_accounts;
```

This query keeps every row but projects only three columns.

## Select columns in the order the reader needs

The order of expressions in the `SELECT` list controls the order of result columns. Place identifiers first, descriptive fields next, and measures or dates where they are easiest to interpret.

For a stakeholder-facing result, this may be clearer:

```sql
SELECT project_id, project_name, due_date, budget_amount
FROM project_register;
```

than placing `budget_amount` before the project identifier.

## Aliases rename result columns

An alias changes the heading shown in the result set without renaming the source column. Use `AS` to make the intention explicit:

```sql
SELECT account_id AS customer_account,
       annual_value AS contract_value
FROM contracts;
```

The source table still contains `account_id` and `annual_value`. Only the result headings change.

Aliases are useful when:

- A source name is technical or unclear.
- A calculated expression needs a readable label.
- Two selected columns would otherwise have confusing names.
- A report requires stakeholder-friendly terminology.

## Alias rules and naming choices

Simple aliases without spaces can be written directly:

```sql
SELECT requested_amount AS request_value
FROM purchase_requests;
```

Aliases containing spaces usually require quoting, and quoting rules differ across database systems. For portable beginner work, prefer `snake_case` aliases such as `monthly_revenue` or `customer_name`.

Avoid aliases that hide meaning. Renaming `monthly_fee` to `value` is technically valid but less informative.

## Worked example 1: make a technical field readable

A quality system stores `defect_qty`, but a report should display `defect_count`:

```sql
SELECT inspection_id,
       defect_qty AS defect_count
FROM quality_inspections;
```

The alias documents the business meaning while preserving the source schema.

## Worked example 2: organize result columns

A staffing analyst wants the employee identifier, display name, and start date:

```sql
SELECT worker_id AS employee_id,
       preferred_name AS employee_name,
       start_date
FROM workforce_roster;
```

The result is structured for a human reader even though the source uses different names.

## `SELECT *` versus an explicit list

`SELECT *` returns all columns. It can help when first inspecting an unfamiliar table:

```sql
SELECT *
FROM vendor_payments;
```

For saved analysis, explicit columns are usually safer because:

- The result does not unexpectedly change when new source columns are added.
- Readers can see which fields the query depends on.
- Sensitive or irrelevant columns are less likely to appear accidentally.
- Downstream tools receive a predictable schema.

## Common mistakes

### Using an alias in the wrong place

This is invalid:

```sql
SELECT order_total AS FROM orders;
```

`AS` must be followed by a valid alias.

### Forgetting that aliases affect only the result

An alias does not permanently rename a database column. A later query must still use the source name unless it defines the alias again.

### Choosing ambiguous aliases

Prefer `order_value` over `value`, and `customer_region` over `region_name` when the context could be unclear.

## Lesson recap

- `SELECT` defines the result columns and their order.
- Explicit column lists are clearer and more stable than `SELECT *`.
- `AS` gives a result column a readable alias.
- Aliases change headings, not source schemas.
- Good aliases preserve business meaning.
