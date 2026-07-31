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

- Return columns in this order: `ticket_id`, `customer_name`, `status`.
- Return 20 rows.

### Task 2

Find the tickets that are still open. Return only `ticket_id`.

**Result requirements**

- Return columns in this order: `ticket_id`.
- Return 6 rows.

### Task 3

Find active tickets that need the fastest attention. Return only `ticket_id` for tickets with High or Urgent priority whose status is Open or Pending.

**Result requirements**

- Return columns in this order: `ticket_id`.
- Return 5 rows.

### Task 4

Find tickets created after June 15, 2026. Return only `ticket_id`.

**Result requirements**

- Return columns in this order: `ticket_id`.
- Return 10 rows.

### Task 5

Review how long closed tickets took to resolve. Return `ticket_id` and `resolution_hours`, sorted from longest to shortest.

**Result requirements**

- Return columns in this order: `ticket_id`, `resolution_hours`.
- Return 11 rows.

### Task 6

Show the five closed tickets with the highest satisfaction scores. Return `ticket_id` and `satisfaction_score`; when scores tie, show the newest ticket first.

**Result requirements**

- Return columns in this order: `ticket_id`, `satisfaction_score`.
- Return 5 rows.

### Task 7

Find open Billing tickets for follow-up. Return only `ticket_id`, sorted from oldest to newest.

**Result requirements**

- Return columns in this order: `ticket_id`.
- Return 4 rows.

## Complete the exercise

1. Complete each task in the SQL editor.
2. Use **Check Task** for specific feedback and hints.
3. Use **Check Exercise** after every task passes.
4. Select **Submit Exercise** to record completion.

