# DuckDB Exercise 20: Inspect data types and work with list values

**Week:** 5
**Estimated time:** 45 minutes
**Concepts:** data types, TRY_CAST, LIST, UNNEST, type-safe calculations

## Purpose

Practice the SQL concepts introduced in the matching DataCamp chapter. Complete the work in your own SQL rather than copying a finished query.

## Available tables

- `ex03_customer_feedback_dirty`

## Scenario

A customer-experience analyst is cleaning mixed data types and grouping issue labels so the records can be summarized safely.

## Tasks

### Task 1

Inspect the source columns and return safe numeric versions of rating and response minutes.

**Result requirements**

- Return columns in this order: `response_id`, `rating`, `response_minutes`.
- Return 18 rows.

### Task 2

Create a list of issue types for each cleaned channel.

**Result requirements**

- Return columns in this order: `channel`, `issue_types`.

### Task 3

Expand the list values back into one row per channel and issue type.

**Result requirements**

- Return columns in this order: `channel`, `issue_type`.

### Task 4

Calculate an average response time using only values that can be converted safely.

**Result requirements**

- Return columns in this order: `average_response_minutes`.
- Return 1 row.

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
