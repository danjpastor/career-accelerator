# DuckDB Exercise 15: Rank results and select top records

**Week:** 5
**Estimated time:** 45 minutes
**Concepts:** ROW_NUMBER, RANK, DENSE_RANK, top-N per group

## Purpose

Practice the SQL concepts introduced in the matching DataCamp chapter. Complete the work in your own SQL rather than copying a finished query.

## Available tables

- `ex10_employees`
- `ex11_tickets`

## Questions

1. Task: Rank all employees from highest to lowest salary using a ranking function that preserves ties. Required output: return only these columns in this order: `employee_id`, `employee_name`, `annual_salary`, `salary_rank`. A correct result contains 12 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
2. Task: Rank employees by salary inside each department. Required output: return only these columns in this order: `employee_id`, `department_id`, `annual_salary`, `department_rank`. A correct result contains 12 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
3. Task: Return the top two salaries in each department using a window rank. Required output: return only these columns in this order: `department_id`, `employee_name`, `annual_salary`, `department_rank`. A correct result contains 8 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
4. Task: Number tickets in opening order for each support agent. Required output: return only these columns in this order: `agent_id`, `ticket_id`, `opened_at`, `ticket_sequence`. A correct result contains 18 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
## Completion evidence

1. Copy `starter.sql` to the DuckDB submissions folder.
2. Answer every question with your own SQL.
3. Use **Check Answer** only after you have attempted the query.
4. Add a short comment describing one mistake you corrected or validation decision you made.
5. Mark the exercise complete only after every checkpoint passes.

## Common mistakes

- Using a concept before its prerequisite chapter is complete.
- Returning the right number of rows with the wrong grain.
- Leaving columns unqualified when more than one table contains the same name.
- Typing expected results instead of deriving them from the data.
