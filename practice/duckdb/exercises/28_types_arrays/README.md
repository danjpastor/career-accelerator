# DuckDB Exercise 20: Inspect data types and work with list values

**Week:** 5
**Estimated time:** 45 minutes
**Concepts:** data types, TRY_CAST, LIST, UNNEST, type-safe calculations

## Purpose

Practice the SQL concepts introduced in the matching DataCamp chapter. Complete the work in your own SQL rather than copying a finished query.

## Available tables

- `ex03_customer_feedback_dirty`

## Questions

1. Task: Inspect the source columns and return safe numeric versions of rating and response minutes. Required output: return only these columns in this order: `response_id`, `rating`, `response_minutes`. A correct result contains 18 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
2. Task: Create a list of issue types for each cleaned channel. Required output: return only these columns in this order: `channel`, `issue_types`. Do not include extra columns; keep every filter and sort rule stated in the task.
3. Task: Expand the list values back into one row per channel and issue type. Required output: return only these columns in this order: `channel`, `issue_type`. Do not include extra columns; keep every filter and sort rule stated in the task.
4. Task: Calculate an average response time using only values that can be converted safely. Required output: return only these columns in this order: `average_response_minutes`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
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
