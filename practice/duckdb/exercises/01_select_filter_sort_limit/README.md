# DuckDB Exercise 01: Filter and sort support tickets

**Week:** 3
**Estimated time:** 35 minutes  
**Concepts:** SELECT, FROM, WHERE, ORDER BY, LIMIT

## Scenario

A customer-support manager is preparing the daily service queue. The manager needs a clear ticket list, the most urgent open work, and a few simple views for follow-up.

## Tables

- `ex01_support_tickets`

## Source CSV files

- `support_tickets.csv`

## Tasks

### Task 1

Prepare the manager's basic ticket list. Return `ticket_id`, `customer_name`, and `status` for every ticket.

**Result requirements**

- **Return columns:** `ticket_id`, `customer_name`, `status`
- **Expected rows:** 20

### Task 2

Find the tickets that are still open. Return only `ticket_id`.

**Result requirements**

- **Return columns:** `ticket_id`
- **Expected rows:** 6

### Task 3

Find active tickets that need the fastest attention. Return only `ticket_id` for tickets with High or Urgent priority whose status is Open or Pending.

**Result requirements**

- **Return columns:** `ticket_id`
- **Expected rows:** 5

### Task 4

Find tickets created after June 15, 2026. Return only `ticket_id`.

**Result requirements**

- **Return columns:** `ticket_id`
- **Expected rows:** 10

### Task 5

Review how long closed tickets took to resolve. Return `ticket_id` and `resolution_hours`, sorted from longest to shortest.

**Result requirements**

- **Return columns:** `ticket_id`, `resolution_hours`
- **Expected rows:** 11

### Task 6

Show the five closed tickets with the highest satisfaction scores. Return `ticket_id` and `satisfaction_score`; when scores tie, show the newest ticket first.

**Result requirements**

- **Return columns:** `ticket_id`, `satisfaction_score`
- **Expected rows:** 5

### Task 7

Find open Billing tickets for follow-up. Return only `ticket_id`, sorted from oldest to newest.

**Result requirements**

- **Return columns:** `ticket_id`
- **Expected rows:** 4
## Completion evidence

1. Copy `starter.sql` to:
   `practice/duckdb/submissions/ex01_select_filter_sort_limit.sql`
2. Answer every question in that copied file.
3. Run each query successfully in DuckDB.
4. Compare your results with `validation.md` only after attempting the questions.
5. Add a short comment at the bottom explaining one decision or mistake you corrected.

The validation file contains result checkpoints, not completed SQL solutions.
