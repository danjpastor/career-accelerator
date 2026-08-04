# Calculate a Three-Day Revenue Average

> **Challenge structure source:** [PostgreSQL Exercises — Calculate a rolling average of total revenue](https://pgexercises.com/questions/aggregates/rollingavg.html)  
> Career Accelerator rebuilt this exercise with original wording, scenario, schema, records, expected output, hints, and solution.

## Scenario

Finance wants daily revenue shown beside a short moving average that smooths normal day-to-day changes.

## Your task

Calculate the three-day rolling average revenue for every date.

## Result requirements

- Return `revenue_date`, `revenue`, and `three_day_average`.
- Round the average to two decimals.
- Sort by `revenue_date`.

## Skill focus

**Window frames and moving averages**

Calculate a rolling metric over the current row and a fixed number of preceding rows.
