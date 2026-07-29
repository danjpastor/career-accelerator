# DuckDB Exercise 21: Rank results and select top records

**Week:** 5
**Estimated time:** 45 minutes
**Concepts:** ROW_NUMBER, RANK, DENSE_RANK, top-N per group

## Purpose

Practice the SQL concepts introduced in the matching DataCamp chapter. Complete the work in your own SQL rather than copying a finished query.

## Available tables

- `ex10_employees`
- `ex11_tickets`

## Questions

1. Rank all employees from highest to lowest salary using a ranking function that preserves ties.
2. Rank employees by salary inside each department.
3. Return the top two salaries in each department using a window rank.
4. Number tickets in opening order for each support agent.

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
