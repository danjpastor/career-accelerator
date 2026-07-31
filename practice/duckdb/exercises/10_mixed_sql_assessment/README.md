# DuckDB Exercise 32: Mixed workforce assessment

**Week:** 6
**Estimated time:** 45 minutes  
**Concepts:** joins, CTEs, window functions, QA, explanation

## Scenario

People Operations needs a workforce assessment combining department budgets, salaries, reporting lines, and performance scores.

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

- Return columns in this order: `employee_id`.
- Return 1 row.

### Task 2

Show workforce cost by department while keeping departments with no employees. Return `department_name`, employee `headcount`, and total `salary_expense`.

**Result requirements**

- Return columns in this order: `department_name`, `headcount`, `salary_expense`.
- Return 4 rows.

### Task 3

Calculate salary expense as a percentage of annual budget for each department. Round to two decimal places and name it `salary_budget_pct`.

**Result requirements**

- Return columns in this order: `department_name`, `salary_budget_pct`.
- Return 4 rows.
- Round the requested result to 2 decimal places.

### Task 4

Use a self join to connect each employee to their manager, then return the number of employee rows as `employee_count`.

**Result requirements**

- Return columns in this order: `employee_count`.
- Return 1 row.

### Task 5

Use a CTE to calculate each employee’s average performance score. Return the number of employees as `employee_count` and the overall average of those scores, rounded to two decimal places, as `average_performance_score`.

**Result requirements**

- Return columns in this order: `employee_count`, `average_performance_score`.
- Return 1 row.
- Round the requested result to 2 decimal places.

### Task 6

Rank employees within each department by average performance using `DENSE_RANK`. Return `employee_id` and the rank as `performance_rank`.

**Result requirements**

- Return columns in this order: `employee_id`, `performance_rank`.
- Return 12 rows.

### Task 7

Return employees whose salary is above their department average.

**Result requirements**

- Return columns in this order: `employee_id`.
- Return 6 rows.

### Task 8

Count employees flagged because they have no department, earn at least 115000, or have an average performance score below 4.0. Return the count as `risk_employee_count`.

**Result requirements**

- Return columns in this order: `risk_employee_count`.
- Return 1 row.

## Complete the exercise

1. Complete each task in the SQL editor.
2. Use **Check Task** for specific feedback and hints.
3. Use **Check Exercise** after every task passes.
4. Select **Submit Exercise** to record completion.

