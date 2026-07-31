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

## Tasks

### Task 1

Count users by acquisition channel.

**Result requirements**

- **Return columns:** `acquisition_channel`, `count_star()`
- **Exact names for new columns:** `count_star()`
- **Expected rows:** 4

### Task 2

Calculate June purchasers and purchaser conversion rate.

**Result requirements**

- **Return columns:** `count(DISTINCT p.user_id)`, `round(((100.0 * count(DISTINCT p.user_id)) / (SELECT count_star() FROM ex09_users)), 2)`
- **Exact names for new columns:** `count(DISTINCT p.user_id)`, `round(((100.0 * count(DISTINCT p.user_id)) / (SELECT count_star() FROM ex09_users)), 2)`
- **Expected rows:** 1

### Task 3

Return users with at least three events.

**Result requirements**

- **Return columns:** `user_id`
- **Expected rows:** 6

### Task 4

Calculate revenue by acquisition channel.

**Result requirements**

- **Return columns:** `acquisition_channel`, `sum(p.amount)`
- **Exact names for new columns:** `sum(p.amount)`
- **Expected rows:** 3

### Task 5

Use a CTE to return each user's first event date and days from signup to first event.

**Result requirements**

- **Return columns:** `count_star()`, `round(avg(date_diff('day', u.signup_date, f.first_event_date)), 2)`
- **Exact names for new columns:** `count_star()`, `round(avg(date_diff('day', u.signup_date, f.first_event_date)), 2)`
- **Expected rows:** 1
## Completion evidence

1. Copy `starter.sql` to:
   `practice/duckdb/submissions/ex09_timed_sql_challenge.sql`
2. Answer every question in that copied file.
3. Run each query successfully in DuckDB.
4. Compare your results with `validation.md` only after attempting the questions.
5. Add a short comment at the bottom explaining one decision or mistake you corrected.

The validation file contains result checkpoints, not completed SQL solutions.
