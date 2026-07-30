# DuckDB Exercise 01: Filter and sort support tickets

**Week:** 3
**Estimated time:** 35 minutes  
**Concepts:** SELECT, FROM, WHERE, ORDER BY, LIMIT

## Scenario

You support a SaaS company. Operations wants a quick view of ticket volume and the most urgent unresolved work.

## Tables

- `ex01_support_tickets`

## Source CSV files

- `support_tickets.csv`

## Questions

1. Task: Return `ticket_id`, `customer_name`, and `status` for every ticket. Required output: return only these columns in this order: `ticket_id`, `customer_name`, `status`. A correct result contains 20 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
2. Task: Return all tickets whose status is `Open`. Required output: return only these columns in this order: `ticket_id`. A correct result contains 6 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
3. Task: Return open or pending tickets with `High` or `Urgent` priority. Required output: return only these columns in this order: `ticket_id`. A correct result contains 5 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
4. Task: Return tickets created after June 15, 2026. Required output: return only these columns in this order: `ticket_id`. A correct result contains 10 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
5. Task: Return closed tickets ordered from longest to shortest `resolution_hours`. Required output: return only these columns in this order: `ticket_id`, `resolution_hours`. A correct result contains 11 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
6. Task: Return the five highest satisfaction scores among closed tickets; break ties by newest `created_at`. Required output: return only these columns in this order: `ticket_id`, `satisfaction_score`. A correct result contains 5 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
7. Task: Return open Billing tickets ordered from oldest to newest. Required output: return only these columns in this order: `ticket_id`. A correct result contains 4 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
## Completion evidence

1. Copy `starter.sql` to:
   `practice/duckdb/submissions/ex01_select_filter_sort_limit.sql`
2. Answer every question in that copied file.
3. Run each query successfully in DuckDB.
4. Compare your results with `validation.md` only after attempting the questions.
5. Add a short comment at the bottom explaining one decision or mistake you corrected.

The validation file contains result checkpoints, not completed SQL solutions.
