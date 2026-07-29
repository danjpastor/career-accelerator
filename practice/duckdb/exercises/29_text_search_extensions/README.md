# DuckDB Exercise 29: Explore text search and extension-safe SQL

**Week:** 6
**Estimated time:** 40 minutes
**Concepts:** ILIKE, regular expressions, text search, extension inspection

## Purpose

Practice the SQL concepts introduced in the matching DataCamp chapter. Complete the work in your own SQL rather than copying a finished query.

## Available tables

- `ex01_support_tickets`
- `ex03_customer_feedback_dirty`

## Questions

1. Find tickets whose customer name contains the word mart without depending on letter case.
2. Find feedback issue values that contain billing after trimming and ignoring case.
3. Use a regular expression to return feedback rows with a four-digit year in the submitted date text.
4. Inspect the extensions known to DuckDB and return their name and loaded status.

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
