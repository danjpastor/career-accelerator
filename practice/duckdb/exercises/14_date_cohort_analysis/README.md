# DuckDB Exercise 21: Build monthly cohorts and retention metrics

**Week:** 5
**Estimated time:** 50 minutes  
**Concepts:** DATE_TRUNC, DATE_DIFF, cohort logic, conditional aggregation

## Scenario

The growth team needs cohort metrics that compare customers from the same signup period using consistent date logic.

## Tables

- `ex14_subscriptions`

## Tasks

### Task 1

Assign each subscription to a signup month using DATE_TRUNC.

**Result requirements**

- **Return columns:** `signup_month`, `subscriptions`
- **Exact names for new columns:** `signup_month`, `subscriptions`
- **Expected rows:** 4

### Task 2

Calculate the number of days from signup to first activation.

**Result requirements**

- **Return columns:** `subscription_id`, `days_to_activation`
- **Exact names for new columns:** `days_to_activation`
- **Expected rows:** 12

### Task 3

Count customers activated within 7 days for each signup cohort.

**Result requirements**

- **Return columns:** `signup_month`, `activated_within_7_days`
- **Exact names for new columns:** `signup_month`, `activated_within_7_days`
- **Expected rows:** 4

### Task 4

Calculate the activation rate within 30 days for each cohort.

**Result requirements**

- **Return columns:** `signup_month`, `activation_rate_30d`
- **Exact names for new columns:** `signup_month`, `activation_rate_30d`
- **Expected rows:** 4

### Task 5

Count cancellations within 60 days of signup by cohort.

**Result requirements**

- **Return columns:** `signup_month`, `cancelled_within_60_days`
- **Exact names for new columns:** `signup_month`, `cancelled_within_60_days`
- **Expected rows:** 4

### Task 6

Calculate active monthly revenue by signup cohort as of 2026-06-30.

**Result requirements**

- **Return columns:** `signup_month`, `active_mrr`
- **Exact names for new columns:** `signup_month`, `active_mrr`
- **Expected rows:** 4

### Task 7

Explain in a SQL comment why cohort metrics need one consistent starting date.

**Result requirements**

- **Return columns:** `count_star()`
- **Exact names for new columns:** `count_star()`
- **Expected rows:** 1
## Completion evidence

1. Work in the standard submission file created by Career Accelerator.
2. Answer every question and run each query successfully.
3. Use `validation.md` only after making a genuine attempt.
4. Add the requested explanation comments in your own words.

The validation file contains result checkpoints, not completed SQL solutions.
