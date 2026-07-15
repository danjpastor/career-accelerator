# DuckDB Exercise 09: Complete a 30-minute product challenge

**Week:** 11  
**Estimated time:** 30 minutes  
**Concepts:** timed aggregation, joins, CASE, CTEs

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

1. Count users by acquisition channel.
2. Calculate June purchasers and purchaser conversion rate.
3. Return users with at least three events.
4. Calculate revenue by acquisition channel.
5. Use a CTE to return each user's first event date and days from signup to first event.

## Completion evidence

1. Copy `starter.sql` to:
   `practice/duckdb/submissions/ex09_timed_sql_challenge.sql`
2. Answer every question in that copied file.
3. Run each query successfully in DuckDB.
4. Compare your results with `validation.md` only after attempting the questions.
5. Add a short comment at the bottom explaining one decision or mistake you corrected.

The validation file contains result checkpoints, not completed SQL solutions.
