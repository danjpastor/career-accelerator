# DuckDB Exercise 32: Complete an end-to-end workforce SQL assessment

**Week:** 7
**Estimated time:** 45 minutes  
**Concepts:** joins, CTEs, window functions, QA, explanation

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

## Tasks

### Task 1

Find employees with missing department assignments.

**Result requirements**

- **Return columns:** `employee_id`
- **Expected rows:** 1

### Task 2

Calculate salary expense and headcount by department, retaining departments with no employees.

**Result requirements**

- **Return columns:** `department_name`, `count(e.employee_id)`, `COALESCE(sum(e.annual_salary), 0)`
- **Exact names for new columns:** `count(e.employee_id)`, `COALESCE(sum(e.annual_salary), 0)`
- **Expected rows:** 4

### Task 3

Calculate department salary expense as a percentage of annual budget.

**Result requirements**

- **Return columns:** `department_name`, `round(((100.0 * sum(e.annual_salary)) / d.annual_budget), 2)`
- **Exact names for new columns:** `round(((100.0 * sum(e.annual_salary)) / d.annual_budget), 2)`
- **Expected rows:** 4

### Task 4

Return each employee's manager name using a self join.

**Result requirements**

- **Return columns:** `count_star()`
- **Exact names for new columns:** `count_star()`
- **Expected rows:** 1

### Task 5

Use a CTE to calculate each employee's average performance score.

**Result requirements**

- **Return columns:** `count_star()`, `round(avg(avg_score), 2)`
- **Exact names for new columns:** `count_star()`, `round(avg(avg_score), 2)`
- **Expected rows:** 1

### Task 6

Rank employees within each department by average performance using `DENSE_RANK`.

**Result requirements**

- **Return columns:** `employee_id`, `dense_rank() OVER (PARTITION BY e.department_id ORDER BY s.avg_score DESC)`
- **Exact names for new columns:** `dense_rank() OVER (PARTITION BY e.department_id ORDER BY s.avg_score DESC)`
- **Expected rows:** 12

### Task 7

Return employees whose salary is above their department average.

**Result requirements**

- **Return columns:** `employee_id`
- **Expected rows:** 6

### Task 8

Create a risk flag for high salary, low performance, or missing department.

**Result requirements**

- **Return columns:** `sum(CASE  WHEN (((e.department_id IS NULL) OR (e.annual_salary >= 115000) OR (s.avg_score < 4.0))) THEN (1) ELSE 0 END)`
- **Exact names for new columns:** `sum(CASE  WHEN (((e.department_id IS NULL) OR (e.annual_salary >= 115000) OR (s.avg_score < 4.0))) THEN (1) ELSE 0 END)`
- **Expected rows:** 1
## Completion evidence

1. Copy `starter.sql` to:
   `practice/duckdb/submissions/ex10_mixed_sql_assessment.sql`
2. Answer every question in that copied file.
3. Run each query successfully in DuckDB.
4. Compare your results with `validation.md` only after attempting the questions.
5. Add a short comment at the bottom explaining one decision or mistake you corrected.

The validation file contains result checkpoints, not completed SQL solutions.
