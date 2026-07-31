# DuckDB Exercise 03: Filter support and feedback records

**Week:** 3
**Estimated time:** 40 minutes
**Concepts:** WHERE, AND, OR, BETWEEN, IN, LIKE, IS NULL

## Purpose

Practice the SQL concepts introduced in the matching DataCamp chapter. Complete the work in your own SQL rather than copying a finished query.

## Available tables

- `ex01_support_tickets`
- `ex03_customer_feedback_dirty`

## Scenario

A support-operations analyst is checking service records before the weekly report is prepared. The analyst needs to identify active priority tickets, missing resolution times, and feedback submitted by email.

## Tasks

### Task 1

List the ticket statuses currently used by the support team. Return each unique `status` in alphabetical order.

**Result requirements**

- **Return columns:** `status`
- **Expected rows:** 3

### Task 2

Find high-priority tickets that are still active. Return `ticket_id`, `priority`, and `status` for High or Urgent tickets that are not Closed.

**Result requirements**

- **Return columns:** `ticket_id`, `priority`, `status`
- **Expected rows:** 5

### Task 3

Find tickets that do not have a recorded resolution time. Return `ticket_id`, `status`, and `resolution_hours`.

**Result requirements**

- **Return columns:** `ticket_id`, `status`, `resolution_hours`
- **Expected rows:** 9

### Task 4

Find feedback submitted through email, even when the channel text uses different capitalization or extra spaces. Return `response_id` and `channel_raw`.

**Result requirements**

- **Return columns:** `response_id`, `channel_raw`
- **Expected rows:** 6
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
