# DuckDB Exercise 25: Explore text search and extension-safe SQL

**Week:** 6
**Estimated time:** 40 minutes
**Concepts:** ILIKE, regular expressions, text search, extension inspection

## Purpose

Practice the SQL concepts introduced in the matching DataCamp chapter. Complete the work in your own SQL rather than copying a finished query.

## Available tables

- `ex01_support_tickets`
- `ex03_customer_feedback_dirty`

## Scenario

A support analyst needs reliable text searches across messy customer and feedback fields and must verify which DuckDB extensions are available.

## Tasks

### Task 1

Find tickets whose customer name contains the word mart without depending on letter case.

**Result requirements**

- Return columns in this order: `ticket_id`, `customer_name`.
- Return 2 rows.

### Task 2

Find feedback issue values that contain billing after trimming and ignoring case.

**Result requirements**

- Return columns in this order: `response_id`, `issue_type_raw`.
- Return 6 rows.

### Task 3

Use a regular expression to return feedback rows with a four-digit year in the submitted date text.

**Result requirements**

- Return columns in this order: `response_id`, `submitted_at_raw`.
- Return 17 rows.

### Task 4

Inspect the extensions known to DuckDB and return their name and loaded status.

**Result requirements**

- Return columns in this order: `extension_name`, `loaded`.

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
