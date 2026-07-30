# DuckDB Exercise 21: Build monthly cohorts and retention metrics

**Week:** 5
**Estimated time:** 50 minutes  
**Concepts:** DATE_TRUNC, DATE_DIFF, cohort logic, conditional aggregation

## Scenario

The growth team needs cohort metrics that compare customers from the same signup period using consistent date logic.

## Tables

- `ex14_subscriptions`

## Questions

1. Task: Assign each subscription to a signup month using DATE_TRUNC. Required output: return only these columns in this order: `signup_month`, `subscriptions`. Use these exact names for calculated or summarized columns: `signup_month`, `subscriptions`. A correct result contains 4 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
2. Task: Calculate the number of days from signup to first activation. Required output: return only these columns in this order: `subscription_id`, `days_to_activation`. Use these exact names for calculated or summarized columns: `days_to_activation`. A correct result contains 12 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
3. Task: Count customers activated within 7 days for each signup cohort. Required output: return only these columns in this order: `signup_month`, `activated_within_7_days`. Use these exact names for calculated or summarized columns: `signup_month`, `activated_within_7_days`. A correct result contains 4 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
4. Task: Calculate the activation rate within 30 days for each cohort. Required output: return only these columns in this order: `signup_month`, `activation_rate_30d`. Use these exact names for calculated or summarized columns: `signup_month`, `activation_rate_30d`. A correct result contains 4 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
5. Task: Count cancellations within 60 days of signup by cohort. Required output: return only these columns in this order: `signup_month`, `cancelled_within_60_days`. Use these exact names for calculated or summarized columns: `signup_month`, `cancelled_within_60_days`. A correct result contains 4 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
6. Task: Calculate active monthly revenue by signup cohort as of 2026-06-30. Required output: return only these columns in this order: `signup_month`, `active_mrr`. Use these exact names for calculated or summarized columns: `signup_month`, `active_mrr`. A correct result contains 4 rows. Do not include extra columns; keep every filter and sort rule stated in the task.
7. Task: Explain in a SQL comment why cohort metrics need one consistent starting date. Required output: return only these columns in this order: `count_star()`. Use these exact names for calculated or summarized columns: `count_star()`. A correct result contains 1 row. Do not include extra columns; keep every filter and sort rule stated in the task.
## Completion evidence

1. Work in the standard submission file created by Career Accelerator.
2. Answer every question and run each query successfully.
3. Use `validation.md` only after making a genuine attempt.
4. Add the requested explanation comments in your own words.

The validation file contains result checkpoints, not completed SQL solutions.
