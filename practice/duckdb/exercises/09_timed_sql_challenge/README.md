# DuckDB Exercise 31: Complete a timed product analysis

**Week:** 7
**Estimated time:** 30 minutes  
**Concepts:** timed SQL analysis, joins, CTEs, business metrics

## Scenario

You have 30 minutes to answer five product-analytics questions. Stop when the timer ends and document unfinished work.

## Tables

- `ex09_users`
- `ex09_events`
- `ex09_purchases`

## Source CSV files

- `events.csv`
- `purchases.csv`
- `users.csv`

## Questions

1. Task: Count users by acquisition channel. Required output: return only these columns in this order: `acquisition_channel`, `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 4 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
2. Task: Calculate June purchasers and purchaser conversion rate. Required output: return only these columns in this order: `count(DISTINCT p.user_id)`, `round(((100.0 * count(DISTINCT p.user_id)) / (SELECT count_star() FROM ex09_users)), 2)`. Use these exact names for calculated or summarized columns: `count(DISTINCT p.user_id)`, `round(((100.0 * count(DISTINCT p.user_id)) / (SELECT count_star() FROM ex09_users)), 2)`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
3. Task: Return users with at least three events. Required output: return only these columns in this order: `user_id`. A correct result contains 6 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
4. Task: Calculate revenue by acquisition channel. Required output: return only these columns in this order: `acquisition_channel`, `sum(p.amount)`. Use these exact names for calculated or summarized columns: `sum(p.amount)`. A correct result contains 3 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
5. Task: Use a CTE to return each user's first event date and days from signup to first event. Required output: return only these columns in this order: `count_star()`, `round(avg(date_diff('day', u.signup_date, f.first_event_date)), 2)`. Use these exact names for calculated or summarized columns: `count_star()`, `round(avg(date_diff('day', u.signup_date, f.first_event_date)), 2)`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
## Completion evidence

1. Copy `starter.sql` to:
   `practice/duckdb/submissions/ex09_timed_sql_challenge.sql`
2. Answer every question in that copied file.
3. Run each query successfully in DuckDB.
4. Compare your results with `validation.md` only after attempting the questions.
5. Add a short comment at the bottom explaining one decision or mistake you corrected.

The validation file contains result checkpoints, not completed SQL solutions.
