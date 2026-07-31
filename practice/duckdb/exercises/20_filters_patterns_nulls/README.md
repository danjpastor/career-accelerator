# DuckDB Exercise 03: Filter patterns, ranges, and missing values

**Week:** 3
**Estimated time:** 40 minutes
**Concepts:** WHERE, AND, OR, BETWEEN, IN, LIKE, IS NULL

## Purpose

Practice the SQL concepts introduced in the matching DataCamp chapter. Complete the work in your own SQL rather than copying a finished query.

## Available tables

- `ex01_support_tickets`
- `ex03_customer_feedback_dirty`

## Scenario

A support-operations analyst is preparing the weekly service report and needs to identify active priority tickets, missing resolution times, and email feedback.

## Tasks

### Task 1

List the ticket statuses currently used by the support team. Return each unique `status` in alphabetical order.

**Result requirements**

- Return columns in this order: `status`.
- Return 3 rows.

### Task 2

Find high-priority tickets that are still active. Return `ticket_id`, `priority`, and `status` for High or Urgent tickets that are not Closed.

**Result requirements**

- Return columns in this order: `ticket_id`, `priority`, `status`.
- Return 5 rows.

### Task 3

Find tickets that do not have a recorded resolution time. Return `ticket_id`, `status`, and `resolution_hours`.

**Result requirements**

- Return columns in this order: `ticket_id`, `status`, `resolution_hours`.
- Return 9 rows.

### Task 4

Find feedback submitted through email, even when the channel text uses different capitalization or extra spaces. Return `response_id` and `channel_raw`.

**Result requirements**

- Return columns in this order: `response_id`, `channel_raw`.
- Return 6 rows.

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
