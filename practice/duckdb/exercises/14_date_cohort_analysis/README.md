# DuckDB Exercise 21: Build monthly cohorts and retention metrics

**Week:** 5
**Estimated time:** 50 minutes  
**Concepts:** DATE_TRUNC, DATE_DIFF, cohort logic, conditional aggregation

## Scenario

The growth team wants to compare subscriptions that began in the same month using consistent activation, cancellation, and revenue definitions.

## Tables

- `ex14_subscriptions`

## Tasks

### Task 1

Assign each subscription to a signup month using DATE_TRUNC.

**Result requirements**

- Return columns in this order: `signup_month`, `subscriptions`.
- Return 4 rows.

### Task 2

Calculate the number of days from signup to first activation.

**Result requirements**

- Return columns in this order: `subscription_id`, `days_to_activation`.
- Return 12 rows.

### Task 3

Count customers activated within 7 days for each signup cohort.

**Result requirements**

- Return columns in this order: `signup_month`, `activated_within_7_days`.
- Return 4 rows.

### Task 4

Calculate the activation rate within 30 days for each cohort.

**Result requirements**

- Return columns in this order: `signup_month`, `activation_rate_30d`.
- Return 4 rows.

### Task 5

Count cancellations within 60 days of signup by cohort.

**Result requirements**

- Return columns in this order: `signup_month`, `cancelled_within_60_days`.
- Return 4 rows.

### Task 6

Calculate active monthly revenue by signup cohort as of 2026-06-30.

**Result requirements**

- Return columns in this order: `signup_month`, `active_mrr`.
- Return 4 rows.

### Task 7

Add a SQL comment explaining why cohort metrics need one consistent starting date, then return the number of cohort rows as `cohort_rows`.

**Result requirements**

- Return columns in this order: `cohort_rows`.
- Return 1 row.

## Complete the exercise

1. Complete each task in the SQL editor.
2. Use **Check Task** for specific feedback and hints.
3. Use **Check Exercise** after every task passes.
4. Select **Submit Exercise** to record completion.

