# One-Value Subqueries

> **Learning goal:** Build scalar subqueries that calculate one benchmark and use it in a normal comparison.

The gentlest subquery returns exactly **one row and one column**. This is called a **scalar subquery**.

Examples of one-value queries include:

```sql
SELECT AVG(salary) FROM employees;
SELECT MAX(amount) FROM orders;
SELECT COUNT(*) FROM customers;
```

Because each result behaves like one value, the outer query can compare against it:

```sql
SELECT department_name, budget
FROM departments
WHERE budget > (
    SELECT AVG(budget)
    FROM departments
);
```

## A reliable five-step process

1. Write the smaller calculation by itself.
2. Run it and confirm that it returns one value.
3. Place parentheses around it.
4. Insert it where a normal value could appear.
5. Run the complete query and explain both stages.

## The result-shape contract

After an operator such as `>`, SQL expects one value:

```sql
WHERE salary > (one value here)
```

This creates a shape mismatch:

```sql
WHERE salary > (
    SELECT salary
    FROM employees
)
```

The inner query may return many salaries, but `>` expects one comparison value. Aggregate functions such as `AVG`, `MIN`, `MAX`, and `COUNT` commonly reduce many rows into one value.

## Filters do not automatically carry inward

Suppose the question is: *Which Atlanta employees earn more than the Atlanta average?*

Both queries need the Atlanta condition because each query answers its own question:

```sql
SELECT employee_name, salary
FROM employees
WHERE city = 'Atlanta'
  AND salary > (
      SELECT AVG(salary)
      FROM employees
      WHERE city = 'Atlanta'
  );
```

The outer filter chooses the rows to return. The inner filter defines the benchmark.

## Common mistakes

- Forgetting the inner query's `FROM` clause.
- Returning many rows where one value is expected.
- Calculating the wrong benchmark because a filter is missing.
- Adding `GROUP BY` when one overall value is required.
- Rounding the benchmark before comparison when exact precision is preferable.

### Quick checkpoint

Before nesting a scalar query, say:

> This query returns one value: __________.

If that sentence is not true, a normal `=`, `>`, or `<` comparison may not be compatible with the result.
