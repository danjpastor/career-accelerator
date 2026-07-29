# DuckDB Exercise 18: Build monthly cohorts and retention metrics

**Week:** 5  
**Estimated time:** 50 minutes  
**Concepts:** DATE_TRUNC, DATE_DIFF, cohort logic, conditional aggregation

## Scenario

The growth team needs cohort metrics that compare customers from the same signup period using consistent date logic.

## Tables

- `ex14_subscriptions`

## Questions

1. Assign each subscription to a signup month using DATE_TRUNC.
2. Calculate the number of days from signup to first activation.
3. Count customers activated within 7 days for each signup cohort.
4. Calculate the activation rate within 30 days for each cohort.
5. Count cancellations within 60 days of signup by cohort.
6. Calculate active monthly revenue by signup cohort as of 2026-06-30.
7. Explain in a SQL comment why cohort metrics need one consistent starting date.

## Completion evidence

1. Work in the standard submission file created by Career Accelerator.
2. Answer every question and run each query successfully.
3. Use `validation.md` only after making a genuine attempt.
4. Add the requested explanation comments in your own words.

The validation file contains result checkpoints, not completed SQL solutions.
