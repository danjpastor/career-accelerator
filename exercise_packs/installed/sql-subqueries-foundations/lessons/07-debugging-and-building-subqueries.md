# Debugging and Building Subqueries

> **Learning goal:** Use a repeatable inside-out workflow to build and debug nested SQL without trying to solve every level at once.

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
WHERE response_minutes > (
    SELECT response_minutes
    FROM service_events
)
```

Ask whether the inner result should be one value or many. If the question needs a benchmark, reduce the rows with `AVG`, `MIN`, or `MAX`.

## Problem: The inner query answers the wrong question

If the task says “priority incidents only,” the benchmark or ID list needs that filter. A query can be syntactically valid and still answer the wrong business question.

## Problem: Aliases are mixed up

```sql
FROM products AS p        -- current outer product
FROM products AS p2       -- rows used for the category benchmark
```

Use role-based aliases and verbalize the connection before nesting.

## Problem: The query is too nested to read

Write each stage separately and label its output. Once correct, consider a CTE so the stages have names.

## Final self-check

Before submitting an answer, say:

- The innermost query returns...
- The next query uses it to...
- The final output contains...

If those sentences are unclear, run the stages separately again.
