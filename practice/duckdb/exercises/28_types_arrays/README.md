# DuckDB Exercise 20: Inspect data types and work with list values

**Week:** 5
**Estimated time:** 45 minutes
**Concepts:** data types, TRY_CAST, LIST, UNNEST, type-safe calculations

## Purpose

Practice the SQL concepts introduced in the matching DataCamp chapter. Complete the work in your own SQL rather than copying a finished query.

## Available tables

- `ex03_customer_feedback_dirty`

## Tasks

### Task 1

Inspect the source columns and return safe numeric versions of rating and response minutes.

**Result requirements**

- **Return columns:** `response_id`, `rating`, `response_minutes`
- **Expected rows:** 18

### Task 2

Create a list of issue types for each cleaned channel.

**Result requirements**

- **Return columns:** `channel`, `issue_types`

### Task 3

Expand the list values back into one row per channel and issue type.

**Result requirements**

- **Return columns:** `channel`, `issue_type`

### Task 4

Calculate an average response time using only values that can be converted safely.

**Result requirements**

- **Return columns:** `average_response_minutes`
- **Expected rows:** 1
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
