# What Is a Subquery?

A **subquery** is a complete SQL query placed inside another SQL query. It lets you break a complex question into smaller questions and use one answer as the input for the next step.

:::columns
:::column
> **Learning Goals:**
> ✓ Recognize a subquery and identify its inner and outer queries.
> ✓ Predict whether the inner query returns one value, a list, or a table.
> ✓ Explain how the outer query uses the inner result.
:::column
```sql
SELECT employee_name, salary
FROM employees
WHERE salary > (
    SELECT AVG(salary)
    FROM employees
);
```
:::

:::columns
:::column
## Example Result

| employee_name | salary |
|---|---:|
| Priya | 91000 |
| Mina | 88000 |
| Chris | 96000 |
| Sam | 105000 |
| Iris | 83000 |

These employees earn more than the company-wide average salary.
:::column
> **Key Idea:** The inner query runs first and returns one value: the average salary. The outer query then uses that value to keep only employees whose salary is greater.
:::

## The two questions inside this query

### 1. Smaller question: What is the average salary?

```sql
SELECT AVG(salary)
FROM employees;
```

This returns **one row and one column**: one number.

### 2. Larger question: Which salaries are greater than that number?

```sql
SELECT employee_name, salary
FROM employees
WHERE salary > (...);
```

The outer query treats the inner result like a value written after `>`.

## The three result shapes

Before nesting anything, determine what the inner query returns.

| Inner result shape | Example | Common outer use |
|---|---|---|
| One value | One average salary | `=`, `>`, `<`, `>=`, `<=` |
| One column with many values | A list of customer IDs | `IN` or `NOT IN` |
| A table | One summary row per department | Put it in `FROM` and give it an alias |

`EXISTS` and `NOT EXISTS` are slightly different: they ask only whether the inner search returns any rows.

## Read from the inside outward

When a nested query looks intimidating, temporarily ignore the outside.

1. What question does the innermost query answer?
2. What columns and rows does it return?
3. Where is that result inserted into the next query?
4. What does the outer query do with it?

Use these two sentences throughout the pack:

- **The inner query returns...**
- **The outer query uses that result to...**

## Why analysts use subqueries

Subqueries help express questions in which one step depends on another result:

- Employees earning more than the company average.
- Customers who placed at least one completed order.
- Departments whose average salary exceeds a benchmark.
- Records for which no related record exists.
- Detailed rows belonging to groups that passed another test.

A subquery is not automatically better than a join or CTE. It is one tool for expressing multi-step logic clearly.

> **First survival rule:** Run the inner query by itself before nesting it. If you cannot explain its output, the complete query will feel much harder than it needs to.

### Quick checkpoint

For the example above, complete these sentences:

- The inner query returns **one value: the company-wide average salary**.
- The outer query uses it to **keep employees whose salary is greater than that value**.
