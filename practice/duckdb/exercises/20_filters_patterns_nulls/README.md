# DuckDB Exercise 03: Filter orders by ranges, patterns, and missing values

**Week:** 3
**Estimated time:** 40 minutes
**Concepts:** WHERE, AND, OR, BETWEEN, IN, LIKE, IS NULL

## Purpose

Practice the SQL concepts introduced in the matching DataCamp chapter. Complete the work in your own SQL rather than copying a finished query.

## Available tables

- `ex01_support_tickets`
- `ex03_customer_feedback_dirty`

## Questions

1. Task: Return the distinct ticket statuses in alphabetical order. Required output: return only these columns in this order: `status`. A correct result contains 3 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
2. Task: Return tickets whose priority is High or Urgent and whose status is not Closed. Required output: return only these columns in this order: `ticket_id`, `priority`, `status`. A correct result contains 5 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
3. Task: Return tickets whose resolution hours are missing. Required output: return only these columns in this order: `ticket_id`, `status`, `resolution_hours`. A correct result contains 9 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
4. Task: Return feedback rows whose raw channel contains the word email after ignoring case and extra spaces. Required output: return only these columns in this order: `response_id`, `channel_raw`. A correct result contains 6 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
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
