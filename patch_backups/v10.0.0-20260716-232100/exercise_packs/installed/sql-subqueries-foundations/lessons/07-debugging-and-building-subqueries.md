# Debugging and Building Subqueries

> **Learning goal:** Use a repeatable inside-out workflow to build and debug nested SQL without trying to solve every level at once.

When a subquery fails, the complete query often hides which stage is wrong. Debug from the inside outward.

## The seven-step workflow

1. Translate the business question into smaller questions.
2. Write the deepest or smallest query first.
3. Run it alone.
4. Check its output shape: one value, one-column list, or table.
5. Insert it into the next query level.
6. Run and inspect that level before adding more nesting.
7. Add final sorting and presentation after the logic works.

## Problem: More than one row where one value is expected

```sql
WHERE salary > (
    SELECT salary
    FROM employees
)
```

Ask: should the inner result be one salary or many? If the question needs a benchmark, reduce the rows with `AVG`, `MIN`, or `MAX`.

## Problem: The inner query answers the wrong question

If the task says “completed orders only,” the benchmark or ID list needs that filter. A query can be syntactically valid and still answer the wrong business question.

## Problem: Aliases are mixed up

In correlated queries, use distinct aliases:

```sql
FROM employees AS e       -- current outer employee
FROM employees AS e2      -- rows used for the benchmark
```

Then verbalize the connection:

> Match the benchmark employee's department (`e2`) to the current employee's department (`e`).

## Problem: Duplicates appear after a join

A join returns matching row combinations. A customer with three orders can appear three times. `IN` and `EXISTS` test membership or existence instead of returning every order row.

## Problem: The query is too nested to read

Write each stage separately and label its output. Once correct, consider a CTE so the stages have names.

## Final self-check

Before checking an answer, say:

- The innermost query returns...
- The next query uses it to...
- The final output contains...

If those sentences are unclear, run the stages separately again. This is normal analytical debugging—not evidence that you are “bad at SQL.”

### Completion checkpoint

You are ready for the capstone when you can identify the output shape of each nested stage before running the full query.
