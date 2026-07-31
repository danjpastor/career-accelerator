# DuckDB Exercise 15: Rank results and select top records

**Week:** 5
**Estimated time:** 45 minutes
**Concepts:** ROW_NUMBER, RANK, DENSE_RANK, top-N per group

## Purpose

Practice the SQL concepts introduced in the matching DataCamp chapter. Complete the work in your own SQL rather than copying a finished query.

## Available tables

- `ex10_employees`
- `ex11_tickets`

## Scenario

People Operations and Support need ranked lists that handle ties correctly and identify the highest-priority records within each group.

## Tasks

### Task 1

Rank all employees from highest to lowest salary using a ranking function that preserves ties.

**Result requirements**

- Return columns in this order: `employee_id`, `employee_name`, `annual_salary`, `salary_rank`.
- Return 12 rows.

### Task 2

Rank employees by salary inside each department.

**Result requirements**

- Return columns in this order: `employee_id`, `department_id`, `annual_salary`, `department_rank`.
- Return 12 rows.

### Task 3

Return the top two salaries in each department using a window rank.

**Result requirements**

- Return columns in this order: `department_id`, `employee_name`, `annual_salary`, `department_rank`.
- Return 8 rows.

### Task 4

Number tickets in opening order for each support agent.

**Result requirements**

- Return columns in this order: `agent_id`, `ticket_id`, `opened_at`, `ticket_sequence`.
- Return 18 rows.

## Complete the exercise

1. Complete each task in the SQL editor.
2. Use **Check Task** for specific feedback and hints.
3. Use **Check Exercise** after every task passes.
4. Select **Submit Exercise** to record completion.

## Common mistakes

- Using a concept before its prerequisite chapter is complete.
- Returning the right number of rows with the wrong grain.
- Leaving columns unqualified when more than one table contains the same name.
- Typing expected results instead of deriving them from the data.
