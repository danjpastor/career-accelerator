# DuckDB Exercise 31: Timed product challenge

**Week:** 6
**Estimated time:** 30 minutes  
**Concepts:** timed SQL analysis, joins, CTEs, business metrics

## Scenario

A product manager needs five quick answers about acquisition, engagement, purchases, and activation. Complete as much as possible within the timed review.

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

Show how many users were acquired through each channel. Return `acquisition_channel` and the count as `user_count`.

**Result requirements**

- Return columns in this order: `acquisition_channel`, `user_count`.
- Return 4 rows.

### Task 2

Count distinct users who made a purchase in June and calculate their share of all users. Return `june_purchasers` and `purchaser_conversion_pct`, rounded to two decimal places.

**Result requirements**

- Return columns in this order: `june_purchasers`, `purchaser_conversion_pct`.
- Return 1 row.
- Round the requested result to 2 decimal places.

### Task 3

Return users with at least three events.

**Result requirements**

- Return columns in this order: `user_id`.
- Return 6 rows.

### Task 4

Show purchase revenue by acquisition channel. Return `acquisition_channel` and total `revenue`.

**Result requirements**

- Return columns in this order: `acquisition_channel`, `revenue`.
- Return 3 rows.

### Task 5

Use a CTE to find each user’s first event date. Return the number of users as `user_count` and average days from signup to first event, rounded to two decimal places, as `average_days_to_first_event`.

**Result requirements**

- Return columns in this order: `user_count`, `average_days_to_first_event`.
- Return 1 row.
- Round the requested result to 2 decimal places.

## Complete the exercise

1. Complete each task in the SQL editor.
2. Use **Check Task** for specific feedback and hints.
3. Use **Check Exercise** after every task passes.
4. Select **Submit Exercise** to record completion.

