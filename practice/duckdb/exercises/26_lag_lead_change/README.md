# DuckDB Exercise 16: Compare current values with prior and next rows

**Week:** 5
**Estimated time:** 45 minutes
**Concepts:** LAG, LEAD, period-over-period change

## Purpose

Practice the SQL concepts introduced in the matching DataCamp chapter. Complete the work in your own SQL rather than copying a finished query.

## Available tables

- `ex15_daily_revenue`

## Questions

1. Task: Add the previous revenue value for the same region to every daily row. Required output: return only these columns in this order: `revenue_date`, `region`, `revenue`, `previous_revenue`. A correct result contains 14 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
2. Task: Calculate day-over-day revenue change for rows that have a prior regional value. Required output: return only these columns in this order: `revenue_date`, `region`, `revenue`, `revenue_change`. A correct result contains 12 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
3. Task: Add the next revenue value for the same region to every daily row. Required output: return only these columns in this order: `revenue_date`, `region`, `revenue`, `next_revenue`. A correct result contains 14 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
4. Task: Calculate the percentage change from the previous regional value and handle the first row safely. Required output: return only these columns in this order: `revenue_date`, `region`, `revenue`, `percent_change`. A correct result contains 14 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
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
