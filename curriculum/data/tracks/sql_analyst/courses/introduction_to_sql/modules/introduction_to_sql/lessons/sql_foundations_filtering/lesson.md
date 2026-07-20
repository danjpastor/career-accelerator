# Filtering, Boolean Logic, and NULL

> **Learning goal:** Translate business rules into precise row filters using comparison operators, `AND`, `OR`, parentheses, `IN`, and correct `NULL` tests.

## WHERE decides which rows qualify

`WHERE` keeps rows that satisfy a condition:

```sql
SELECT request_id, status
FROM maintenance_requests
WHERE status = 'Open';
```

The selected columns control the result shape; the `WHERE` clause controls row eligibility.

## Comparison operators express thresholds and boundaries

| Operator | Meaning | Example |
|---|---|---|
| `=` | equal to | `status = 'Open'` |
| `<>` or `!=` | not equal to | `status <> 'Closed'` |
| `>` | greater than | `amount > 100` |
| `>=` | greater than or equal to | `amount >= 100` |
| `<` | less than | `days_open < 7` |
| `<=` | less than or equal to | `days_open <= 7` |

Boundary words matter. “At least 100” means `>= 100`; “more than 100” means `> 100`.

Text values are usually enclosed in single quotes:

```sql
WHERE approval_status = 'Approved'
```

## AND requires every condition to be true

```sql
SELECT request_id, urgency, status
FROM maintenance_requests
WHERE status = 'Open'
  AND urgency = 'High';
```

A row qualifies only if both conditions are true.

## OR accepts any listed condition

```sql
SELECT request_id, status
FROM maintenance_requests
WHERE status = 'Open'
   OR status = 'Pending';
```

A row qualifies if either condition is true.

For several accepted values in the same column, `IN` is often clearer:

```sql
WHERE status IN ('Open', 'Pending')
```

## Parentheses protect mixed Boolean logic

`AND` is evaluated before `OR` in SQL. A business rule such as “Open or Pending tickets that are Urgent” should be grouped explicitly:

```sql
WHERE (status = 'Open' OR status = 'Pending')
  AND priority = 'Urgent'
```

Without parentheses, the query can include rows the stakeholder did not request. Parentheses make both the logic and the reader's intention clear.

## NULL means unknown or missing

`NULL` is not equal to any value, including another `NULL`. Use `IS NULL` or `IS NOT NULL`:

```sql
SELECT survey_id, rating
FROM customer_surveys
WHERE rating IS NULL;
```

This is incorrect:

```sql
WHERE rating = NULL
```

A missing value should not automatically be interpreted as zero, blank text, or false. Its business meaning depends on the field.

## Worked example 1: inclusive threshold

A procurement analyst needs approved requests worth at least 5,000:

```sql
SELECT request_id, requested_amount
FROM purchase_requests
WHERE approval_status = 'Approved'
  AND requested_amount >= 5000;
```

The phrase “at least” requires `>=`.

## Worked example 2: mixed Boolean logic

A facilities manager wants active buildings that are overdue or unassigned:

```sql
SELECT inspection_id, building_id, due_date
FROM inspections
WHERE active_building = TRUE
  AND (due_date < CURRENT_DATE OR inspector_id IS NULL);
```

The parentheses ensure the active-building rule applies to both alternatives.

## Common mistakes

- Writing `= NULL` instead of `IS NULL`.
- Forgetting quotes around text values.
- Using `OR` when every condition must be true.
- Mixing `AND` and `OR` without parentheses.
- Choosing `>` when the threshold should include the boundary.
- Filtering on a result alias that is not available in `WHERE` in the current SQL dialect.

## Translate English into logic step by step

For the request “unresolved High or Urgent tickets assigned to Technical”:

1. Define unresolved: `status IN ('Open', 'Pending')`.
2. Define accepted priorities: `priority IN ('High', 'Urgent')`.
3. Define the team: `assigned_team = 'Technical'`.
4. Connect all required groups with `AND`.

```sql
WHERE status IN ('Open', 'Pending')
  AND priority IN ('High', 'Urgent')
  AND assigned_team = 'Technical'
```

## Lesson recap

- `WHERE` controls which rows are returned.
- Comparison operators must match the wording of the business rule.
- `AND` requires all conditions; `OR` accepts alternatives.
- Parentheses are essential when combining `AND` and `OR`.
- Use `IS NULL` and `IS NOT NULL` for missing values.
