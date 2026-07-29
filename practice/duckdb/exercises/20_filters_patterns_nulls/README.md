# DuckDB Exercise 04: Filter patterns, ranges, and missing values

**Week:** 3
**Estimated time:** 40 minutes
**Concepts:** WHERE, AND, OR, BETWEEN, IN, LIKE, IS NULL

## Purpose

Practice the SQL concepts introduced in the matching DataCamp chapter. Complete the work in your own SQL rather than copying a finished query.

## Available tables

- `ex01_support_tickets`
- `ex03_customer_feedback_dirty`

## Questions

1. Return the distinct ticket statuses in alphabetical order.
2. Return tickets whose priority is High or Urgent and whose status is not Closed.
3. Return tickets whose resolution hours are missing.
4. Return feedback rows whose raw channel contains the word email after ignoring case and extra spaces.

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
