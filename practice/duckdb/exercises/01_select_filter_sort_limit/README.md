# DuckDB Exercise 01: Filter and sort support tickets

**Week:** 1  
**Estimated time:** 35 minutes  
**Concepts:** SELECT, FROM, WHERE, ORDER BY, LIMIT

## Scenario

You support a SaaS company. Operations wants a quick view of ticket volume and the most urgent unresolved work.

## Tables

- `ex01_support_tickets`

## Source CSV files

- `support_tickets.csv`

## Questions

1. Return `ticket_id`, `customer_name`, and `status` for every ticket.
2. Return all tickets whose status is `Open`.
3. Return open or pending tickets with `High` or `Urgent` priority.
4. Return tickets created after June 15, 2026.
5. Return closed tickets ordered from longest to shortest `resolution_hours`.
6. Return the five highest satisfaction scores among closed tickets; break ties by newest `created_at`.
7. Return open Billing tickets ordered from oldest to newest.

## Completion evidence

1. Copy `starter.sql` to:
   `practice/duckdb/submissions/ex01_select_filter_sort_limit.sql`
2. Answer every question in that copied file.
3. Run each query successfully in DuckDB.
4. Compare your results with `validation.md` only after attempting the questions.
5. Add a short comment at the bottom explaining one decision or mistake you corrected.

The validation file contains result checkpoints, not completed SQL solutions.
