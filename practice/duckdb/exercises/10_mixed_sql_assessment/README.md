# DuckDB Exercise 10: Complete a mixed workforce assessment

**Week:** 12  
**Estimated time:** 45 minutes  
**Concepts:** NULLs, joins, aggregation, CTEs, ranking

## Scenario

People Operations needs a workforce assessment combining budgets, salaries, reporting lines, and performance.

## Tables

- `ex10_departments`
- `ex10_employees`
- `ex10_performance_reviews`

## Source CSV files

- `departments.csv`
- `employees.csv`
- `performance_reviews.csv`

## Questions

1. Find employees with missing department assignments.
2. Calculate salary expense and headcount by department, retaining departments with no employees.
3. Calculate department salary expense as a percentage of annual budget.
4. Return each employee's manager name using a self join.
5. Use a CTE to calculate each employee's average performance score.
6. Rank employees within each department by average performance using `DENSE_RANK`.
7. Return employees whose salary is above their department average.
8. Create a risk flag for high salary, low performance, or missing department.

## Completion evidence

1. Copy `starter.sql` to:
   `practice/duckdb/submissions/ex10_mixed_sql_assessment.sql`
2. Answer every question in that copied file.
3. Run each query successfully in DuckDB.
4. Compare your results with `validation.md` only after attempting the questions.
5. Add a short comment at the bottom explaining one decision or mistake you corrected.

The validation file contains result checkpoints, not completed SQL solutions.
